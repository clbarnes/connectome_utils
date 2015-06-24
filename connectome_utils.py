import networkx as nx
from graph_tool import generation


def split_on_edge_attribute(G, attribute):
    split_graphs = dict()
    for edge in G.edges_iter(data=True):
        this_edge_attr = edge[2][attribute]
        if this_edge_attr in split_graphs:
            split_graphs[this_edge_attr].add_edge(edge[0], edge[1], **edge[2])
        else:
            split_graphs[this_edge_attr] = nx.create_empty_copy(G, with_nodes=False)
            split_graphs[this_edge_attr].add_nodes_from(G.nodes(data=True))
            split_graphs[this_edge_attr].add_edge(edge[0], edge[1], **edge[2])

    return split_graphs


def split_on_node_attribute(G, attribute):
    split_graphs = dict()
    for edge in G.edges_iter(data=True):
        node1, node2 = edge[0:2]
        attr_values = []
        for node in node1, node2:
            attr_values.append(G.node[node][attribute])
            if attr_values[-1] in split_graphs:
                split_graphs[attr_values[-1]].add_node(node, G.node[node])
            else:
                split_graphs[attr_values[-1]] = nx.create_empty_copy(G, with_nodes=False)
                split_graphs[attr_values[-1]].add_node(node, G.node[node])

        if attr_values[0] == attr_values[1]:
            split_graphs[attr_values[0]].add_edge(edge[0], edge[1], **edge[2])

    return split_graphs


def split_on_node_attribute_including_interclass(G, attribute):
    split_graphs = dict()
    for edge in G.edges_iter(data=True):
        node1, node2 = edge[0:2]
        attr_values = []
        for node in node1, node2:
            attr_values.append(G.node[node][attribute])
            if attr_values[-1] in split_graphs:
                split_graphs[attr_values[-1]].add_node(node, G.node[node])
            else:
                split_graphs[attr_values[-1]] = nx.create_empty_copy(G, with_nodes=False)
                split_graphs[attr_values[-1]].add_node(node, G.node[node])

        if attr_values[0] == attr_values[1]:
            split_graphs[attr_values[0]].add_edge(edge[0], edge[1], **edge[2])

    return split_graphs


def collapse_LR(G, side='L'):
    if side not in ['L', 'R']:
        raise ValueError("Argument 'side' must be either 'L' or 'R', was {}.".format(side))

    G2 = nx.create_empty_copy(G, with_nodes=False)
    node_names = dict()
    node_set = set(G2.nodes())
    for node, data in G.nodes_iter(data=True):
        if (node.endswith('L') and node[:-1] + 'R' in node_set) \
                or (node.endswith('R') and node[:-1] + 'L' in node_set):
            node_names[node] = node[:-1]
            if node[-1] == side:
                G2.add_node(node[:-1], data)
        else:
            node_names[node] = node
            G2.add_node(node, data)

    for src_node, tgt_node, data in G.edges_iter(data=True):
        G2.add_edge(node_names[src_node], node_names[tgt_node], **data)

    return G2


def knockout(graph, receptor=None, transmitter=None):
    if receptor is None and transmitter is None:
        raise ValueError('Must select a receptor or transmitter to knock out!')

    G = nx.create_empty_copy(graph, with_nodes=False)
    G.add_nodes_from(graph.nodes_iter(data=True))

    for src, tgt, data in graph.edges_iter(data=True):
        if receptor is not None and 'receptor' in data and data['receptor'] == receptor:
            continue

        if transmitter is not None and 'transmitter' in data and data['transmitter'] == transmitter:
            continue

        G.add_edge(src, tgt, attr_dict=data)

    return G


def randomise(graph, keep_labels=False):
    if graph.is_directed():
        return randomise_di(graph, keep_labels)
    else:
        return randomise_undi(graph, keep_labels)


def degree_generator_di(graph):
    in_deg = graph.in_degree()
    out_deg = graph.out_degree()

    for node in sorted(graph.nodes_iter()):
        yield in_deg[node], out_deg[node]


def randomise_di(graph, keep_labels):
    gen = degree_generator_di(graph)
    gt_graph = generation.random_graph(graph.number_of_nodes(), deg_sampler=lambda: next(gen), self_loops=True)
    out_graph = nx.DiGraph()

    if keep_labels:
        nodes = sorted(graph.nodes_iter())
        out_graph.add_nodes_from(nodes)

        for edge in gt_graph.edges():
            out_graph.add_edge(nodes[int(edge.source())], nodes[int(edge.target())])
    else:
        out_graph.add_nodes_from(int(vert) for vert in gt_graph.vertices())
        for edge in gt_graph.edges():
            out_graph.add_edge(int(edge.source()), int(edge.target()))

    return out_graph


def degree_generator_undi(graph):
    deg = graph.degree()
    for node in sorted(graph.nodes_iter()):
        yield deg[node]


def randomise_undi(graph, keep_labels):
    gen = degree_generator_undi(graph)
    gt_graph = generation.random_graph(graph.number_of_nodes(), deg_sampler=lambda: next(gen), directed=False, self_loops=True)
    out_graph = nx.Graph()

    if keep_labels:
        nodes = sorted(graph.nodes_iter())
        out_graph.add_nodes_from(nodes)

        for edge in gt_graph.edges():
            out_graph.add_edge(nodes[int(edge.source())], nodes[int(edge.target())])
    else:
        out_graph.add_nodes_from(int(vert) for vert in gt_graph.vertices())
        for edge in gt_graph.edges():
            out_graph.add_edge(int(edge.source()), int(edge.target()))

    return out_graph