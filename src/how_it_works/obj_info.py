import ast
from dataclasses import dataclass, field


@dataclass
class ObjInfo:
    absolute_name: str
    node: ast.AST
    alias: str = field(default='')
