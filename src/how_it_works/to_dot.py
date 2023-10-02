import networkx as nx


def render(ntx: nx.DiGraph) -> None:
    dot = nx.nx_agraph.to_agraph(ntx)
    dot.write()
