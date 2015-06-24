import networkx as nx
import connectome_utils as util


class MultiplexConnectome():

    def __init__(self, data_source):
        if isinstance(data_source, str):
            self.whole = nx.read_gpickle(data_source)
        elif isinstance(data_source, nx.Graph):
            self.whole = data_source.copy()
        else:
            raise ValueError('Unrecognised data source type: {}'.format(type(data_source)))

        self.sub = util.split_on_edge_attribute(self.whole, 'type')

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
            composed.add_edges_from(self[name].edges(data=True) for name in args)

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