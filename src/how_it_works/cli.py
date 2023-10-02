import logging
from collections import defaultdict
from pathlib import Path

import click

from how_it_works import graph, to_dot, visitor


@click.command()
@click.option('--root', required=True)
@click.option('--entry-point', required=True)
@click.option('--verbose', '-v', is_flag=True)
def main(root: str, entry_point: str, verbose: bool) -> None:
    if verbose:
        logging.basicConfig(format='')
        visitor.logger.setLevel(logging.INFO)

    full_path = Path(root) / entry_point
    parts = list(Path(entry_point).parts)
    if len(parts):
        parts[-1] = Path(parts[-1]).stem
    calls = defaultdict(list)
    for c in visitor.visit('.'.join(parts), str(full_path)):
        calls[c.ctx].append(c.target)

    ntx = graph.parse(calls)
    graph.remove_hyper_connect(ntx)
    to_dot.render(ntx)
    # print(ast.dump(tree, indent=2))
