import ast
from queue import Queue
from dataclasses import dataclass

from how_it_works.utils import get_path_from_absolute_name, load_tree


class TreeIterator:
    def __init__(self, root: ast.AST) -> None:
        self.q: Queue[ast.AST] = Queue()
        self.q.put_nowait(root)

    def __iter__(self):
        return self

    def __next__(self):
        while not self.q.empty():
            node = self.q.get_nowait()
            yield node
            for field, value in ast.iter_fields(node):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, ast.AST):
                            self.q.put_nowait(item)
                elif isinstance(value, ast.AST):
                    self.q.put_nowait(value)
        raise StopIteration


@dataclass(frozen=True)
class ImportInfo:
    is_star: bool
    alias: str
    absolute_name: str


def analyze_import(node: ast.AST) -> ImportInfo:
    path = get_path_from_absolute_name(absolute_name)
    return load_tree(path)


@dataclass(frozen=True)
class FuncDefInfo:
    alias: str
    absolute_name: str


def analyze_func_def(node: ast.AST) -> FuncDefInfo:
    pass
