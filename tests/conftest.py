import logging
import sys
from os.path import dirname
from pathlib import Path
from typing import Callable

import pytest

from how_it_works import visitor


@pytest.fixture()
def run(request) -> Callable[[str, str], dict]:
    def runner(src: str, endpoint: str) -> set[str]:
        logging.basicConfig(format='')
        visitor.logger.setLevel(logging.INFO)
        absolute_src_path = str(Path(dirname(request.node.fspath)) / src)

        edges = set()
        visitor.Visitor.clear()
        for c in visitor.visit(absolute_src_path, endpoint, 0):
            edges.add(f'{c.ctx} -> {c.target}')

        return edges

    return runner
