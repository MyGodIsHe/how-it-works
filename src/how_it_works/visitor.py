import ast
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from importlib.machinery import ExtensionFileLoader
from importlib.util import find_spec
from typing import Any, Callable

logger = logging.getLogger(__name__)
SyncAsyncFuncDef = ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(frozen=True)
class Call:
    ctx: str
    target: str

    def __str__(self) -> str:
        return f'{self.ctx} -> {self.target}'


class Visitor(ast.NodeVisitor):
    import_def_visits: dict[str, 'Visitor | None'] = {}
    calls: list[Call] = []
    inside_import = False

    def __init__(self, target: str, depth: int, max_depth: int) -> None:
        self.ctx = CallContext(target)
        self.target = target
        self.depth = depth
        self.max_depth = max_depth
        self.alias: dict[str, Alias] = {}

    @classmethod
    def clear(cls) -> None:
        cls.import_def_visits = {}
        cls.calls = []
        cls.inside_import = False

    def visit_Import(self, node: ast.Import) -> Any:
        for n in node.names:
            object_dot_path = self.get_absolute_path(n.name)
            alias = n.name or n.asname
            assert alias is not None
            self.alias[alias] = Alias(full_name=object_dot_path)
            self.real_visit_import(n.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        for n in node.names:
            object_dot_path = self.get_absolute_path(f'{node.module or self.target}.{n.name}')
            is_duck = n.name == '*'
            if not is_duck:
                alias = n.name or n.asname
                assert alias is not None
                self.alias[alias] = Alias(full_name=object_dot_path)
            v = self.real_visit_import(object_dot_path)
            if is_duck and v:
                self.alias.update(v.alias)

    def real_visit_import(self, module_dot_path: str) -> 'Visitor | None':
        module_path, module_dot_path = get_module_path(module_dot_path)
        if module_path is None:
            return None
        if module_dot_path in self.import_def_visits:
            v = self.import_def_visits[module_dot_path]
        else:
            self.import_def_visits[module_dot_path] = None  # import cycle protect
            with self.mark_import():
                v = _visit(module_dot_path, module_path, self.max_depth, self.depth + 1)
            self.import_def_visits[module_dot_path] = v
        return v

    def get_absolute_path(self, module_dot_path: str) -> str:
        if module_dot_path.startswith('.'):
            return f'{self.target}.{module_dot_path}'
        return module_dot_path

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
                if self.ctx.is_cyclic:
                    return
                self.visit(sub_node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.visit_sync_async_func_def(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        # TODO: учитывать await
        self.visit_sync_async_func_def(node)

    def real_visit_func_def(self, node: SyncAsyncFuncDef) -> None:
        alias = self.alias.get(node.name)
        with self.ctx(alias.full_name):
            if self.ctx.is_cyclic:
                return
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
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                instance_alias = self.get_alias_and_visit_call(node.func.value.id, skip_call=True)
                # нужно asyncio.run транслировать как-то в asyncio.main.run
                # self.get_absolute_path(f'{instance_alias}.{node.func.attr}')
                call_target = self.get_alias_and_visit_call(f'{instance_alias}.{node.func.attr}')
        if isinstance(node.func, ast.Name):
            call_target = self.get_alias_and_visit_call(node.func.id)
        if call_target and not self.inside_import:
            call = Call(ctx=self.ctx.current, target=call_target)
            self.calls.append(call)
        self.generic_visit(node)

    def get_alias_and_visit_call(self, alias_name: str, skip_call: bool = False) -> str:
        alias = self.alias.get(alias_name)
        if alias:
            if not skip_call and alias.lazy_visitor:
                alias.lazy_visitor()
            return alias.full_name
        return alias_name

    @classmethod
    @contextmanager
    def mark_import(cls):
        prev = cls.inside_import
        cls.inside_import = True
        yield
        cls.inside_import = prev


class CallContext:
    def __init__(self, target: str) -> None:
        self.stack: list[str] = [target]

    @property
    def current(self) -> str:
        return self.stack[-1]

    @property
    def is_cyclic(self) -> bool:
        return self.stack[-1] in self.stack[:-1] if self.stack else False

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
    module_path, name = get_module_path(name)
    if module_path is None:
        # TODO: print cli error
        return []
    v = _visit(name, module_path, max_depth)
    if v is None:
        return []
    return v.calls


def _visit(name: str, path: str, max_depth: int, import_depth: int = 0) -> Visitor | None:
    if 0 < max_depth < import_depth:
        return None

    with log_visit(import_depth, name):
        with open(path, 'r') as f:
            source = f.read()
        v = Visitor(name, import_depth, max_depth)
        tree = ast.parse(source, path)
        v.visit(tree)
        return v


@contextmanager
def log_visit(depth: int, name: str):
    offset = ' ' * depth * 2
    logger.info(f'{offset}v {name}')
    yield
    logger.info(f'{offset}^ {name}')


def get_module_path(name: str) -> tuple[str | None, str]:
    if name == '__main__':
        return None, name

    while True:
        try:
            spec = find_spec(name)
            break
        except ModuleNotFoundError:
            n = name.rfind('.')
            if n == -1:
                # maybe need raise
                return None, name
            name = name[:n]

    if spec is None:
        return None, name
    if isinstance(spec.loader, ExtensionFileLoader):
        return None, name
    path = spec.origin

    if path in ('built-in', 'frozen'):
        return None, name

    return path, name
