import networkx as nx
from pyvis.network import Network

color_filter = {
    'menus': 'red',
    'loader': 'purple',
    'forms': 'darkblue',
    'popups': 'blue',
    'default': 'black',

}


def render(file_name: str, ntx: nx.DiGraph, root=None, size0=5, loosen=2) -> None:
    nt = Network(width='1200px', height='800px', directed=True)
    for node in ntx.nodes:
        mass = ntx.nodes[node]['size'] / (loosen * size0)
        size = size0 * ntx.nodes[node]['size'] ** 0.5
        label = node
        color = color_filter['default']
        for key in color_filter:
            if key in node:
                color = color_filter[key]
        kwargs = {
            'label': label,
            'mass': mass,
            'size': size,
            'color': color,
        }
        nt.add_node(node, **kwargs, )

    for link in ntx.edges:
        # depth = nx.shortest_path_length(ntx, source=root, target=link[0])
        # print(link, depth)
        # width = max(size0, size0 * (12 - 4 * depth))

        nt.add_edge(link[0], link[1])

    nt.show_buttons(filter_=['physics'])
    nt.show(file_name, notebook=False)
