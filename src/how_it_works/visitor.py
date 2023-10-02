import ast
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from importlib.machinery import ExtensionFileLoader
from importlib.util import find_spec
from typing import Any


logger = logging.getLogger(__name__)


class Visitor(ast.NodeVisitor):
    imports: set[str] = set()

    def __init__(self, target: str, depth) -> None:
        self.calls: list[Call] = []
        self.ctx = CallContext(target)
        self.target = target
        self.depth = depth

    def visit_Import(self, node: ast.Import) -> Any:
        for n in node.names:
            import_path = self.fix_import(n.name)
            if import_path not in self.imports:
                self.imports.add(import_path)
                self.calls.extend(visit(import_path, depth=self.depth + 1))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        for n in node.names:
            import_path = self.fix_import(f'{node.module or self.target}.{n.name}')
            if import_path not in self.imports:
                self.imports.add(import_path)
                self.calls.extend(visit(import_path, depth=self.depth + 1))

    def fix_import(self, name: str) -> str:
        if name.startswith('.'):
            name = f'{self.target}.{name}'
        if name.endswith('*'):
            name = name[:-2]
        return name

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        for item in node.decorator_list:
            if isinstance(item, ast.AST):
                self.visit(item)
        with self.ctx(node.name):
            for item in node.body:
                if isinstance(item, ast.AST):
                    self.visit(item)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        # TODO: учитывать await
        self.visit_FunctionDef(node)

    def visit_Call(self, node: ast.Call) -> Any:
        match type(node.func):
            case ast.Attribute:
                match type(node.func.value):
                    case ast.Name:
                        call_target = f'{node.func.value.id}.{node.func.attr}'
                        self.calls.append(Call(ctx=self.ctx.current, target=call_target))
            case ast.Name:
                call_target = f'{node.func.id}'
                self.calls.append(Call(ctx=self.ctx.current, target=call_target))
        self.generic_visit(node)


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
        return self.stack[-1]

    @contextmanager
    def __call__(self, target: str):
        self.stack.append(target)
        yield
        self.stack.pop()


def visit(name: str, path: str = None, depth: int = 0) -> list[Call]:
    if name == '__main__':
        return []

    if path is None:
        try:
            spec = find_spec(name)
        except ModuleNotFoundError:
            return []
        if spec is None:
            return []
        if isinstance(spec.loader, ExtensionFileLoader):
            return []
        path = spec.origin

    if path in ('built-in', 'frozen'):
        return []

    with log_visit(depth, name):
        with open(path, 'r') as f:
            source = f.read()
        v = Visitor(name, depth)
        tree = ast.parse(source, path)
        v.visit(tree)
        return v.calls


@contextmanager
def log_visit(depth: int, name: str):
    offset = ' ' * depth * 2
    logger.info(f'{offset}v {name}')
    yield
    logger.info(f'{offset}^ {name}')
