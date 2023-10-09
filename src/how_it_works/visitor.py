import ast
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from importlib.machinery import ExtensionFileLoader
from importlib.util import find_spec
from typing import Any, Callable

logger = logging.getLogger(__name__)
SyncAsyncFuncDef = ast.FunctionDef | ast.AsyncFunctionDef


class Visitor(ast.NodeVisitor):
    visits: dict[str, 'Visitor | None'] = {}

    def __init__(self, target: str, depth: int, max_depth: int) -> None:
        self.calls: list[Call] = []
        self.ctx = CallContext(target)
        self.target = target
        self.depth = depth
        self.max_depth = max_depth
        self.alias: dict[str, Alias] = {}

    def visit_Import(self, node: ast.Import) -> Any:
        for n in node.names:
            self.add_import(n.name, n.name or n.asname)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        for n in node.names:
            self.add_import(f'{node.module or self.target}.{n.name}', n.name or n.asname)

    def add_import(self, name: str, alias_name: str) -> None:
        """
        Добавить псевдонимы и посетить модуль
        """
        import_path = name
        if import_path.startswith('.'):
            import_path = f'{self.target}.{import_path}'

        is_duck = import_path.endswith('*')
        if is_duck:
            import_path = import_path[:-2]
        else:
            self.alias[alias_name] = Alias(full_name=import_path)

        if import_path in self.visits:
            v = self.visits[import_path]
        else:
            self.visits[import_path] = None  # import cycle protect
            v = _visit(import_path, import_depth=self.depth + 1, max_depth=self.max_depth)
            self.visits[import_path] = v
        if v:
            self.calls.extend(v.calls)
            if is_duck:
                self.alias.update(v.alias)

    def fix_import(self, name: str) -> str:
        if name.startswith('.'):
            name = f'{self.target}.{name}'
        if name.endswith('*'):
            name = name[:-2]
        return name

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        self.alias[node.name] = Alias(full_name=f'{self.target}.{node.name}')
        for item in node.decorator_list:
            if isinstance(item, ast.AST):
                self.visit(item)
        for sub_node in node.body:
            with self.ctx(node.name):
                self.visit(sub_node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.visit_sync_async_func_def(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        # TODO: учитывать await
        self.visit_sync_async_func_def(node)

    def real_visit_func_def(self, node: SyncAsyncFuncDef) -> None:
        with self.ctx(node.name):
            for item in node.body:
                if isinstance(item, ast.AST):
                    self.visit(item)

    def visit_sync_async_func_def(self, node: SyncAsyncFuncDef) -> None:
        self.alias[node.name] = Alias(
            full_name=f'{self.target}.{node.name}',
            lazy_visitor=lambda: self.real_visit_func_def(node),
        )
        for item in node.decorator_list:
            if isinstance(item, ast.AST):
                self.visit(item)

    def visit_Call(self, node: ast.Call) -> Any:
        call_target = None
        match type(node.func):
            case ast.Attribute:
                match type(node.func.value):
                    case ast.Name:
                        call_target = self.get_alias_and_call(node.func.value.id)
                        call_target = f'{call_target}.{node.func.attr}'
            case ast.Name:
                call_target = self.get_alias_and_call(node.func.id)
        if call_target:
            self.calls.append(Call(ctx=self.ctx.current, target=call_target))
        self.generic_visit(node)

    def get_alias_and_call(self, alias_name: str) -> str:
        alias = self.alias.get(alias_name)
        if alias:
            if alias.lazy_visitor:
                alias.lazy_visitor()
            return alias.full_name
        return alias_name


@dataclass
class Call:
    ctx: str
    target: str

    def __str__(self) -> str:
        return f'{self.ctx} -> {self.target}'


class CallContext:
    def __init__(self, target: str) -> None:
        self.stack: list[str] = [target]

    @property
    def current(self) -> str:
        return '.'.join(self.stack)

    @contextmanager
    def __call__(self, target: str):
        self.stack.append(target)
        yield
        self.stack.pop()


@dataclass
class Alias:
    full_name: str
    lazy_visitor: Callable[[], None] | None = field(default=None)


def visit(name: str, max_depth: int) -> list[Call]:
    v = _visit(name, max_depth=max_depth)
    if v is None:
        return []
    return v.calls


def _visit(name: str, path: str = None, import_depth: int = 0, max_depth: int = 0) -> Visitor | None:
    if 0 < max_depth < import_depth:
        return None

    if name == '__main__':
        return None

    if path is None:
        try:
            spec = find_spec(name)
        except ModuleNotFoundError:
            return None
        if spec is None:
            return None
        if isinstance(spec.loader, ExtensionFileLoader):
            return None
        path = spec.origin

    if path in ('built-in', 'frozen'):
        return None

    with log_visit(import_depth, name):
        with open(path, 'r') as f:
            source = f.read()
        v = Visitor(name, import_depth, max_depth)
        tree = ast.parse(source, path)
        # print(ast.dump(tree, indent=2))
        v.visit(tree)
        return v


@contextmanager
def log_visit(depth: int, name: str):
    offset = ' ' * depth * 2
    logger.info(f'{offset}v {name}')
    yield
    logger.info(f'{offset}^ {name}')
