import networkx as nx
import connectome_utils as util


class MultiplexConnectome():

    def __init__(self, data_source, edge_category_attribute='etype'):
        if isinstance(data_source, str):
            self.whole = nx.read_gpickle(data_source)
        elif isinstance(data_source, nx.Graph):
            self.whole = data_source.copy()
        else:
            raise ValueError('Unrecognised data source type: {}'.format(type(data_source)))

        self.sub = util.split_on_edge_attribute(self.whole, edge_category_attribute)

    def __getitem__(self, item):
        return self.sub[item]

    def compose(self, *args):
        """
        Compose specified subgraphs into a single MultiDiGraph().

        :param args: Names of subgraphs to compose
        :return: nx.MultiDiGraph
        """
        if len(args) == 0:
            args = list(self.sub)

        composed = self[args[0]].copy()

        if len(args) > 1:
            for name in args[1:]:
                composed.add_edges_from(self[name].edges(data=True))

        return composed

    def collapse(self, *args):
        """
        Collapse specified subgraphs into a single DiGraph (i.e. multi-edges are collapsed into a single edge of increased weight)

        :param args: Names of subgraphs to collapse.
        :return: Single graph containing all of the information of the specified graphs
        :rtype: nx.DiGraph
        """
        if len(args) == 0:
            args = list(self.sub)

        composed = self.compose(*args) if len(args) > 1 else self[args[0]].copy()

        G = nx.DiGraph()
        G.add_nodes_from(composed.nodes())

        for start in composed.edge:
            for stop in composed.edge[start]:
                G.add_edge(start, stop, attr_dict=collapse_edge_data(composed.edge[start][stop].values()))

        return G

    def expand(self, *args):
        """

        :param args: Names of subgraphs to collapse (default all)
        :return: Graph with all edges representing multiple connections (i.e. with a weight greater than 1) split into multiple edges
        """
        if len(args) == 0:
            G = self.whole
        else:
            G = self.compose(*args)

        G2 = nx.create_empty_copy(G, with_nodes=True)

        for src, tgt, data in G.edges_iter(data=True):
            data2 = data.copy()
            data2['weight'] = 1
            G2.add_edges_from([(src, tgt)]*data['weight'], data2)

        return G2


def collapse_edge_data(dicts):
    keys = {key for d in dicts for key in d}
    collapsed = {key: [] for key in keys}
    for d in dicts:
        for key in keys:
            collapsed[key].append(d.get(key, None))

    try:
        collapsed['length'] = [length for length in collapsed['length'] if length is not None][0]
    except KeyError:
        pass
    collapsed['summed_weight'] = sum([weight for weight in collapsed['weight'] if weight is not None])

    return collapsed


def expand_edges(G, weight='weight'):
    G2 = nx.MultiDiGraph()

    for node, data in G.nodes(data=True):
        G2.add_node(node, attr_dict=data)

    for src, tgt, key, data in G.edges_iter(keys=True, data=True):
        copies = data.get(weight, 1)
        data2 = data
        data2[weight] = 1
        for i in range(copies):
            G2.add_edge(src, tgt, key='{}_{}'.format(key, i+1), attr_dict=data2)

    return G2


def collapse_edges(G, condition=None, weight='weight'):
    G2 = nx.MultiDiGraph()

    for node, data in G.nodes_iter(data=True):
        G2.add_node(node, attr_dict=data)

    edgeset = set(G.edges_iter())

    if condition is None:
        for src, tgt in edgeset:
            weight_val = sum([data.get(weight, 1) for data in G.edge[src][tgt].values()])
            G2.add_edge(src, tgt, key='{}->{}'.format(src, tgt), attr_dict={weight: weight_val})
    else:
        for src, tgt in edgeset:
            cond_values = {data.get(condition) for data in G.edge[src][tgt].values()}
            for cond_value in cond_values:
                G2.add_edge(src, tgt, key='{}_{}->{}'.format(cond_value, src, tgt), attr_dict={weight: 0})
            for data in G.edge[src][tgt].values():
                cond_value = data.get(condition)
                G.edge[src][tgt]['{}_{}->{}'.format(cond_value, src, tgt)][weight] += data.get(weight, 1)

    return G2