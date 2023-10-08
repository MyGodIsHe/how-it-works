import networkx as nx


def parse(data: dict) -> nx.DiGraph:
    graph = nx.DiGraph()

    for node, children in data.items():
        graph.add_node(node)
        for child in children:
            graph.add_edge(node, child)

    return graph


def remove_hyper_connect(ntx: nx.DiGraph, threshold=5) -> None:
    to_remove = []
    for node in ntx.nodes:
        if len(list(ntx.predecessors(node))) >= threshold:
            to_remove.append(node)

    for node in to_remove:
        ntx.remove_node(node)
