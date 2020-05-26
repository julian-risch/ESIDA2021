import logging
import re
from collections import defaultdict
from typing import List, Callable, Tuple
import numpy as np
import data.models as models
from common import init_or_get_fasttext_model, init_or_get_toxicity_model
from data.processors import Modifier, GraphRepresentationType
from scipy import sparse
from fast_pagerank import pagerank, pagerank_power


logger = logging.getLogger('data.graph.ranking')


def build_edge_dict(graph):
    dic = defaultdict(list)
    for e in graph.edges:
        if e not in dic[e.src]:
            dic[e.src].append(e)
        if e not in dic[e.tgt]:
            dic[e.tgt].append(e)
    return dic


class SizeRanker(Modifier):
    def __init__(self, *args, **kwargs):
        """
        Returns a graph with page-ranked node weights
        :param args:
        :param num_iterations: number of iteration for PageRank
        :d: d parameter for PageRank
        :normalize: normalize the PageRank values?
        :param kwargs:
        """
        super().__init__(*args, **kwargs)

        logger.debug(f'{self.__class__.__name__} initialised')

    def modify(self, graph: GraphRepresentationType):
        for comment in graph.comments:
            for split in comment.splits:
                split.wgts.SIZE = split.e-split.s


class VotesRanker(Modifier):
    def __init__(self, *args, use_upvotes=None, use_downvotes=None, **kwargs):
        """
        Returns a graph with page-ranked node weights
        :param args:
        :param num_iterations: number of iteration for PageRank
        :d: d parameter for PageRank
        :normalize: normalize the PageRank values?
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.use_upvotes = self.conf_getboolean('use_upvotes', use_upvotes)
        self.use_downvotes = self.conf_getboolean('use_downvotes', use_downvotes)
        logger.debug(f'{self.__class__.__name__} initialised '
                     f'use_upvotes={self.use_upvotes}'
                     f'use_downvotes={self.use_downvotes}')

    def modify(self, graph: GraphRepresentationType):
        for comment in graph.comments:
            vote_sum = 0
            orig_comment = graph.orig_comments[graph.id2idx[comment.id]]
            if self.use_upvotes:
                if orig_comment.upvotes:
                    vote_sum += orig_comment.upvotes
                if orig_comment.leseempfehlungen:
                    vote_sum += orig_comment.leseempfehlungen
                if orig_comment.likes:
                    vote_sum += orig_comment.likes
                if orig_comment.love:
                    vote_sum += orig_comment.love
                if orig_comment.recommended:
                    vote_sum += orig_comment.recommended
            if self.use_downvotes:
                if orig_comment.downvotes:
                    vote_sum += orig_comment.downvotes

            for split in comment.splits:
                split.wgts.VOTES = vote_sum


class RecencyRanker(Modifier):
    def __init__(self, *args, use_yongest=None, **kwargs):
        """
        Returns a graph with page-ranked node weights
        :param args:
        :param num_iterations: number of iteration for PageRank
        :d: d parameter for PageRank
        :normalize: normalize the PageRank values?
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.use_yongest = self.conf_getboolean('use_yongest', use_yongest)
        logger.debug(f'{self.__class__.__name__} initialised')

    def modify(self, graph: GraphRepresentationType):
        if self.use_yongest:
            agr_timestamp = max([graph.orig_comments[graph.id2idx[comment.id]].timestamp for comment in graph.comments])
            comparison_factor = -1
        else:
            agr_timestamp = min([graph.orig_comments[graph.id2idx[comment.id]].timestamp for comment in graph.comments])
            comparison_factor = 1

        for comment in graph.comments:
            orig_comment = graph.orig_comments[graph.id2idx[comment.id]]
            for split in comment.splits:
                split.wgts.RECENCY = comparison_factor*(orig_comment.timestamp-agr_timestamp).total_seconds()


class PageRanker(Modifier):
    def __init__(self, *args, num_iterations: int = None, d: float = None, edge_type=None,
                 user_power_mode=None, **kwargs):
        """
        Returns a graph with page-ranked node weights
        :param args:
        :param num_iterations: number of iteration for PageRank
        :d: d parameter for PageRank
        :normalize: normalize the PageRank values?
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.num_iterations = self.conf_getint('num_iterations', num_iterations)
        self.d = self.conf_getfloat('d', d)
        self.edge_type = self.conf_get('edge_type', edge_type)
        self.use_power_mode = self.conf_getboolean('use_power_mode', user_power_mode)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'num_iterations={self.num_iterations}, d={self.d} and use_power_mode={self.use_power_mode}')

    def page_rank_fast(self, graph: GraphRepresentationType):
        def edge_list_to_adjacency_list(edge_type):
            adjacency_weights = []
            adjacency_edges = []

            node_counter = 0
            node_index = {}
            for c in graph.comments:
                for split_id, _ in enumerate(c.splits):
                    node_index[(graph.id2idx[c.id], split_id)] = node_counter
                    node_counter += 1
            for e in graph.edges:
                weight = e.wgts[edge_type]
                if weight:
                    adjacency_edges.append([node_index[e.src], node_index[e.tgt]])
                    adjacency_weights.append(weight)

            return np.array(adjacency_edges), adjacency_weights, node_index

        adjacency_matrix, weights, int_index = edge_list_to_adjacency_list(self.edge_type)
        csr_graph = sparse.csr_matrix((weights, (adjacency_matrix[:, 0], adjacency_matrix[:, 1])),
                                      shape=(len(int_index.keys()), len(int_index.keys())))

        if self.use_power_mode:
            pr = pagerank_power(csr_graph, p=self.d, tol=1e-6, max_iter=self.num_iterations)
        else:
            pr = pagerank(csr_graph, p=self.d)

        # update node of graph with new weights for PageRank
        counter = 0
        for comment in graph.comments:
            for j, split in enumerate(comment.splits):
                split.wgts.PAGERANK = pr[counter]
                counter += 1

    def modify(self, graph: GraphRepresentationType):
        self.page_rank_fast(graph)


class CentralityDegreeCalculator(Modifier):
    def __init__(self, *args, **kwargs):
        """
        Returns a graph with page-ranked node weights
        :param args:
        :param num_iterations: number of iteration for PageRank
        :d: d parameter for PageRank
        :normalize: normalize the PageRank values?
        :param kwargs:
        """
        super().__init__(*args, **kwargs)

        logger.debug(f'{self.__class__.__name__} initialised')

    def modify(self, graph: GraphRepresentationType):
        counter_dict = defaultdict(int)
        for edge in graph.edges:
            counter_dict[edge.tgt] += 1
            counter_dict[edge.src] += 1
        # update node of graph with new weights for degree centrality
        for comment in graph.comments:
            for j, split in enumerate(comment.splits):
                split.wgts.DEGREE_CENTRALITY = counter_dict[(graph.id2idx[comment.id], j)]


class ToxicityRanker(Modifier):
    def __init__(self, *args, window_length=None, whole_comment=None, **kwargs):
        """
        Returns a graph with toxicity node weights
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.window_length = self.conf_getint('window_length', window_length)
        self.whole_comment = self.conf_getboolean('whole_comment', whole_comment)
        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'window_length={self.window_length} and '
                     f'whole_comment={self.whole_comment}. '
                     f'Load ft model...')
        ft_model = init_or_get_fasttext_model()
        self.ft_model = ft_model
        self.n_features = ft_model.get_dimension()
        logger.debug(f'ft model loaded with {self.n_features} features. '
                     f'Load toxicity model...')
        self.toxicity_model = init_or_get_toxicity_model()
        logger.debug(f'toxicity model loaded.')

    def normalize(self, s):
        # transform to lowercase characters
        s = str(s)
        # s = s.lower()
        # Isolate punctuation
        s = re.sub(r'([\'\"\.\(\)\!\?\-\\\/\,])', r' \1 ', s)
        # Remove some special characters
        s = re.sub(r'([\;\:\|\n])', ' ', s)
        return s

    def text_to_vector(self, text):
        """
        Given a string, normalizes it, then splits it into words and finally converts
        it to a sequence of word vectors.
        """
        text = self.normalize(text)
        words = text.split()
        window = words[-self.window_length:]
        x = np.zeros((self.window_length, self.n_features))
        for i, word in enumerate(window):
            x[i, :] = self.ft_model.get_word_vector(word).astype('float32')
        return x

    def orig_comment_to_data(self, comments: List[models.CommentCached]):
        """
        Convert a given list of original_comment to a dataset of inputs for the NN.
        """
        x = np.zeros((len(comments), self.window_length, self.n_features), dtype='float32')

        for i, comment in enumerate(comments):
            x[i, :] = self.text_to_vector(comment.text)
        return x

    def graph_comments_to_data(self, graph: GraphRepresentationType):
        """
        Convert a graph with slitted comments to a dataset of inputs for the NN.
        """
        number_of_data_points = 0
        for comment in graph.comments:
            for _ in comment.splits:
                number_of_data_points += 1

        x = np.zeros((number_of_data_points, self.window_length, self.n_features), dtype='float32')

        index = 0
        for comment in graph.comments:
            for split in comment.splits:
                text = graph.orig_comments[graph.id2idx[comment.id]].text[int(split.s): int(split.e)]
                x[index, :] = self.text_to_vector(text)
                index += 1
        return x

    def modify(self, graph: GraphRepresentationType):
        # for orig_comments
        if self.whole_comment:
            x = self.orig_comment_to_data(graph.orig_comments)
            predictions = self.toxicity_model.predict(x, verbose=0, batch_size=512)

            for comment_counter, comment in enumerate(graph.comments):
                for split in comment.splits:
                    split.wgts.TOXICITY = predictions[comment_counter][0]
        # for sentences
        else:
            x = self.graph_comments_to_data(graph)

            predictions = self.toxicity_model.predict(x, verbose=0, batch_size=512)

            split_counter = 0
            for comment in graph.comments:
                for split in comment.splits:
                    # use probability for not being toxic
                    split.wgts.TOXICITY = predictions[split_counter][0]
                    split_counter += 1

