import networkx as nx


def threshold_contact_number(graph, minimum):
    """
    Copies input graph and removes edges between nodes if the summed weight of all edges between those same nodes is less than minimum.

    :param graph: Graph
    :type graph: networkx.Graph
    :param minimum: Only edges which form part of a multi-edge with weight greater than this should remain
    :type minimum: int or float
    :return: Graph
    :rtype: nx.Graph
    """
    G = nx.MultiDiGraph()
    contact_number = dict()

    for node in graph.nodes_iter(data=True):
        G.add_node(node[0], node[1])

    for edge in graph.edges_iter(data=True):
        if (edge[0], edge[1]) not in contact_number:
            contact_number[(edge[0], edge[1])] = 0

        contact_number[(edge[0], edge[1])] += edge[2]['weight'] if 'weight' in edge[2] else 1

    for edge in graph.edges_iter(data=True):
        if contact_number[(edge[0], edge[1])] >= minimum:
            G.add_edge(edge[0], edge[1], attr_dict=edge[2])

    return G


def generate_paths(G, attr_name, src_attr, tgt_attr, cutoff):
    """

    :param G: Graph
    :type G: networkx.Graph
    :param attr_name: Name of node attribute whose value is the category separating nodes into source and target
    :type attr_name: hashable
    :param src_attr: Value of attr_name attribute for source nodes
    :type src_attr: hashable
    :param tgt_attr: Value of attr_name attribute for target nodes
    :type tgt_attr: hashable
    :param cutoff: Maximum path length
    :type cutoff: int
    :return: All paths from source to target nodes below criterion length
    :rtype: dict from source nodes to (dicts from target nodes to (lists of (lists of nodes forming a path)))
    """
    paths = dict()

    for src_node in get_nodes_with_attribute(G, attr_name, src_attr):
        if src_node not in paths:
            paths[src_node] = dict()

        for tgt_node in get_nodes_with_attribute(G, attr_name, tgt_attr):
            paths[src_node][tgt_node] = list(nx.all_simple_paths(G, src_node, tgt_node, cutoff=cutoff))

    return paths


def get_nodes_with_attribute(G, attr_name, attr_value, data=False):
    return (node if data else node[0]
            for node in G.nodes_iter(data=True)
            if attr_name in node[1] and node[1][attr_name] == attr_value)


def izq_beer_constraints(G):
    G2 = threshold_contact_number(G, 2)
    paths = generate_paths(G2, 'type', 'sensory', 'motor', 3)

    return G2, paths


def is_fully_connected(paths, src_set=None, tgt_set=None):
    """

    :param paths: Path mapping
    :type paths: dict from src_node to (dict from tgt_node to list)
    :param src_set: Nodes to act as sources
    :type src_set: list
    :param tgt_set: Nodes to act as targets
    :type tgt_set: list
    :return: Whether all source nodes have a path to all target nodes
    :rtype: bool
    """

    if src_set is None:
        src_set = paths.values()

    for d in src_set:
        for path_list in tgt_set if tgt_set else d.values():
            if not path_list:
                return False

    return True


def remove_unconnected_nodes(G):
    """

    :param G: Graph
    :type G: networkx.Graph
    :return: A copy of G with all unconnected nodes removed
    :rtype: networkx.Graph
    """
    G_out = G.copy()

    for node, degree in G_out.degree().items():
        if degree == 0:
            G_out.remove_node(node)

    return G_out


def remove_unnecessary_edges(G, paths_ddl):
    """

    :param G: Graph
    :type G: networkx.Graph
    :param paths_ddl:
    :type paths_ddl: dict from source nodes to (dicts from target nodes to (lists of (lists of nodes forming a path)))
    :return: Copy of G with all edges not involved in the specified path removed
    :rtype: networkx.Graph
    """
    G_out = G.copy()

    edge_set = set()

    for path in (path for d in paths_ddl.values() for l in d.values() for path in l if path):
        for edge in zip(path, path[1:]):
            edge_set.add(edge)

    for edge in G_out.edges():
        if edge not in edge_set:
            while True:
                try:
                    G_out.remove_edge(*edge)
                except nx.NetworkXError:
                    break

    return G_out