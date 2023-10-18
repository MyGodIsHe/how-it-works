import ast
from typing import Iterator

from how_it_works.obj_info import ObjInfo
from how_it_works.tree_tools import TreeIterator


class Scope:
    def __init__(self, root: ast.AST, full_name: str) -> None:
        self.full_name = full_name
        self._tree_iter: Iterator[ast.AST] = TreeIterator(root)
        self._alias_map: dict[str, ObjInfo] = {}

    def add_obj_info(self, info: ObjInfo) -> None:
        self._alias_map[info.alias] = info

    def get_obj_info(self, alias: str) -> ObjInfo | None:
        return self._alias_map.get(alias)

    def get_next_node(self) -> ast.AST | None:
        try:
            return next(self._tree_iter)
        except StopIteration:
            return None


class ImportScope:
    def __init__(self, root: ast.AST, full_name: str) -> None:
        self.full_name = full_name
        self._tree_iter: Iterator[ast.AST] = TreeIterator(root)
        self._alias_map: dict[str, ObjInfo] = {}


def join_scopes(parent_scope: Scope | None, child_name: str) -> str:
    if parent_scope:
        return f'{parent_scope.full_name}.{child_name}'
    return child_name
