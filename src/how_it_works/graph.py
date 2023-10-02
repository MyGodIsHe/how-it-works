import networkx as nx


def parse(data: dict) -> nx.DiGraph:
    nt = nx.DiGraph()

    def _ensure_key(name):
        if name not in nt:
            nt.add_node(name, size=50)

    for node in data:
        _ensure_key(node)
        for child in data[node]:
            _ensure_key(child)
            nt.add_edge(node, child)
    return nt


def remove_hyper_connect(ntx: nx.DiGraph, threshold=5) -> None:
    to_remove = []
    for node in ntx.nodes:
        if len(list(ntx.predecessors(node))) >= threshold:
            to_remove.append(node)

    for node in to_remove:
        ntx.remove_node(node)
