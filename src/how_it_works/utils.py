import ast
from importlib.machinery import ExtensionFileLoader
from importlib.util import find_spec


def get_path_from_absolute_name(name: str) -> str | None:
    if name == '__main__':
        return None

    while True:
        try:
            spec = find_spec(name)
            break
        except ModuleNotFoundError:
            n = name.rfind('.')
            if n == -1:
                # maybe need raise
                return None
            name = name[:n]

    if spec is None:
        return None
    if isinstance(spec.loader, ExtensionFileLoader):
        return None
    path = spec.origin

    if path in ('built-in', 'frozen'):
        return None

    return path


def load_tree(path: str) -> ast.AST:
    with open(path) as f:
        data = f.read()
    return ast.parse(data, path)
