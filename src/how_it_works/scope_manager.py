import ast

from how_it_works.obj_info import ObjInfo
from how_it_works.scope import Scope


class ScopeManager:
    def __init__(self) -> None:
        self._scopes: list[Scope] = []

    @property
    def current(self) -> Scope | None:
        if not self._scopes:
            return None
        return self._scopes[-1]

    def enter_to_child_scope(self, info: ObjInfo) -> None:
        s = Scope(info.node, info.absolute_name)
        self._scopes.append(s)

    def exit_from_current_scope(self) -> None:
        self._scopes.pop()
