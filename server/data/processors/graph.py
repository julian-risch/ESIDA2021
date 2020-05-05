from data.processors import modification
from data.processors.text import split_comment
import data.models as models
from typing import List
from data.processors.structure import SameArticleComparator, SameCommentComparator, ReplyToComparator, SimilarityComparator
from data.processors.modification import PageRanker, PageRankFilter, CentralityDegreeCalculator, SimilarityEdgeFilter, BottomReplyToEdgeFilter
from configparser import ConfigParser
from common import config
#from tqdm import tqdm
import logging

COMPARATORS = [SameArticleComparator,
               SameCommentComparator,
               ReplyToComparator,
               #SimilarityComparator
               ]

MODIFIERS = [BottomReplyToEdgeFilter]

logger = logging.getLogger('data.processors.graph')


class GraphRepresentation:
    def __init__(self, comments: List[models.CommentCached], conf: dict = None):
        # create a temporary copy of the global config
        self.conf = ConfigParser()
        self.conf.read_dict(config)
        if conf is not None:
            self.conf.read_dict(conf)

        # full text comments might be needed by comparator
        self.orig_comments = comments

        # data for models.Graph
        self.comments = [split_comment(comment) for comment in comments]
        self.id2idx = {}
        self.edges = []
        self.nodes = []

        logger.debug(f'{len(self.comments)} comments turned '
                     f'into {len([s for c in self.comments for s in c.splits])} splits')

        # construct graph
        self._build_index()
        self._pairwise_comparisons()
        # self._modify()

    def __dict__(self) -> models.Graph.__dict__:
        return {
            'comments': self.comments,
            'id2idx': self.id2idx,
            'edges': self.edges
        }

    def _build_index(self):
        for i, comment in enumerate(self.comments):
            self.id2idx[comment.id] = i

    def _pairwise_comparisons(self):
        comparators = [comparator(conf=self.conf) for comparator in COMPARATORS if comparator.is_on(self.conf)]

        for i in (range(len(self.comments))):
            comment_i = self.comments[i]
            orig_comment_i = self.orig_comments[i]
            for si in range(len(comment_i.splits)):
                for j in range(i, len(self.comments)):
                    comment_j = self.comments[j]
                    orig_comment_j = self.orig_comments[j]
                    # if comparing sentences within the same comment, skip lower triangle
                    for sj in range(si + 1 if i == j else 0, len(comment_j.splits)):
                        weights = []
                        for comparator in comparators:
                            result = comparator.compare(orig_comment_i, comment_i,
                                                        orig_comment_j, comment_j, si, sj)
                            if result:
                                weights = models.EdgeWeights()
                                weights[comparator.edge_type()] = result
                                # weights.append(result)
                        if weights:
                            self.edges.append(models.Edge(src=[i, si],
                                                          tgt=[j, sj],
                                                          wgts=weights))

    def _modify(self):
        modification.Modifier.use(modifiers_to_use=MODIFIERS, graph_to_modify=self, conf=self.conf)
