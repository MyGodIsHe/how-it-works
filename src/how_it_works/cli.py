import logging
import sys

import click
import networkx as nx

from how_it_works import to_dot, visitor


@click.command()
@click.option('--src', required=True, help='root dir of source code')
@click.option('--endpoint', required=True, help='import path')
@click.option('--max-depth', type=int, default=0)
@click.option('--verbose', '-v', is_flag=True)
@click.option('--dry-run', is_flag=True)
def main(src: str, endpoint: str, max_depth: int, verbose: bool, dry_run: bool) -> None:
    logging.basicConfig(format='')
    if verbose:
        visitor.logger.setLevel(logging.INFO)

    graph = nx.DiGraph()
    for c in visitor.visit(src, endpoint, max_depth):
        graph.add_edge(c.ctx, c.target)

    if not dry_run:
        to_dot.render(graph)


if __name__ == '__main__':
    main()
