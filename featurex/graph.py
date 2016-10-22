from featurex.extractors import Extractor
from featurex.transformers import get_transformer
from itertools import chain
from featurex.utils import listify
from six import string_types
from collections import OrderedDict


class Node(object):

    ''' A graph node/vertex. Represents a single transformer, optionally with
    references to children.
    Args:
        name (str): Name of the node
        transformer (Transformer): the Transformer instance at this node
    '''

    def __init__(self, name, transformer):
        self.name = name
        self.children = []
        if isinstance(transformer, string_types):
            transformer = get_transformer(transformer)
        self.transformer = transformer

    def collect(self, stim):
        if hasattr(self, 'transformer') and self.transformer is not None:
            if isinstance(self.transformer, Extractor):
                return [self.transformer.transform(stim)]
            stim = self.transformer.transform(stim)
        return list(chain(*[c.collect(stim) for c in self.children]))
   
    def add_child(self, node):
        ''' Append a child to the list of children. '''
        self.children.append(node)

    def is_leaf(self):
        return len(self.children) > 0


class Graph(Node):

    def __init__(self, nodes):

        self.nodes = OrderedDict()
        self.children = []
        self.add_children(nodes)

    def add_branch(self, nodes, parent=None):
        for n in nodes:
            node_args = self._parse_node_args(n)
            node = self.add_node(parent=parent, return_node=True, **node_args)
            parent = node

    def add_children(self, nodes, parent=None):
        for n in nodes:
            node_args = self._parse_node_args(n)
            self.add_node(parent=parent, **node_args)

    @staticmethod
    def _parse_node_args(node):

        if isinstance(node, dict):
            return node

        kwargs = {}

        if isinstance(node, (list, tuple)):
            kwargs['transformer'] = node[0]
            if len(node) > 1:
                kwargs['name'] = node[1]
            if len(node) > 2:
                kwargs['children'] = node[2]
        else:
            kwargs['transformer'] = node

        return kwargs

    def add_node(self, transformer, name=None, children=None, parent=None,
                 return_node=False):

        if name is None:
            name = id(transformer)

        node = Node(name, transformer)
        self.nodes[name] = node

        parent = self if parent is None else self.nodes[parent]
        parent.add_child(node)

        if children is not None:
            for c in children:
                c_kwargs = self._parse_node_args(c)
                self.add_node(parent=node, **c)

        if return_node:
            return node

    def extract(self, stims):
        stims = listify(stims)
        return [self.collect(s) for s in stims][0]

    def _validate(self):
        # Make sure all connected node inputs and outputs match
        pass