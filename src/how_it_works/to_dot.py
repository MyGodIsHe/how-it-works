import networkx as nx


def render(ntx: nx.DiGraph) -> None:
    ntx.graph['graph'] = {
        'rankdir': 'LR',
    }
    dot = nx.nx_agraph.to_agraph(ntx)
    dot.write()
