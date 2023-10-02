import json

import click

from how_it_works import graph, to_html


@click.command()
@click.option('--graph-path', required=True)
def main(graph_path: str) -> None:
    with open(graph_path, 'r') as fin:
        data = json.load(fin)

    ntx = graph.parse(data)
    graph.remove_hyper_connect(ntx)
    to_html.render('nodes.html', ntx)
