from data.processors import ranking
from data.processors.text import split_comment
import data.models as models
from typing import List
from data.processors import GraphRepresentationType
from data.processors.structure import SameArticleComparator, SameCommentComparator, ReplyToComparator, TemporalComparator
from data.processors.embedding import SimilarityComparator
from data.processors.ranking import PageRanker, CentralityDegreeCalculator, SizeRanker, VotesRanker, RecencyRanker
from data.processors.filters import *


from configparser import ConfigParser
from common import config
import logging

COMPARATORS = [
    SameArticleComparator,
    SameCommentComparator,
    ReplyToComparator,
    SimilarityComparator,
    TemporalComparator
]

MODIFIERS = [
    # edge and node weighting
    PageRanker,
    CentralityDegreeCalculator,
    SizeRanker,
    VotesRanker,
    RecencyRanker,

    # filtering
    GenericEdgeFilter, SimilarityEdgeFilter, ReplyToEdgeFilter, SameCommentEdgeFilter, SameArticleEdgeFilter,
    SameGroupEdgeFilter, TemporalEdgeFilter, OrEdgeFilter,
    GenericBottomEdgeFilter, BottomSimilarityEdgeFilter, BottomReplyToEdgeFilter, BottomTemporalEdgeFilter,
    BottomSameCommentFilter, BottomSameArticleEdgeFilter, BottomSameGroupEdgeFilter,
    GenericNodeWeightFilter, SizeFilter, PageRankFilter, DegreeCentralityFilter,
    RecencyFilter, VotesFilter, ToxicityFilter,
    GenericNodeWeightBottomFilter, SizeBottomFilter, PageRankBottomFilter, DegreeCentralityBottomFilter,
    RecencyBottomFilter, VotesBottomFilter, ToxicityBottomFilter
]

logger = logging.getLogger('data.processors.graph')


class GraphRepresentation(GraphRepresentationType):
    def __init__(self, comments: List[models.CommentCached], conf: dict = None):
        super().__init__(comments)


        # create a temporary copy of the global config
        self.conf = ConfigParser()
        self.conf.read_dict(config)
        if conf is not None:
            self.conf.read_dict(conf)
        self.comments: List[models.SplitComment] = [split_comment(comment) for comment in comments]

        # config: configuration from DEFAULT.ini
        # self.conf: configuration from code
        # FIXME: delete, due this is only for testing purposes because the code config overrides the configuration from file
        self.conf = config

        logger.debug(f'{len(self.comments)} comments turned '
                     f'into {len([s for c in self.comments for s in c.splits])} splits')

        # construct graph
        self._build_index()
        self._pairwise_comparisons()
        self._modify()

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
                        edge_weights = models.EdgeWeights()

                        for comparator in comparators:
                            comparator.update_edge_weights(edge_weights,
                                                           orig_comment_i, comment_i,
                                                           orig_comment_j, comment_j, si, sj)
                        if edge_weights.dict(exclude_unset=True):
                            self.edges.append(models.Edge(src=[i, si],
                                                          tgt=[j, sj],
                                                          wgts=edge_weights))

    def _modify(self):
        modifiers = [modifier(conf=self.conf) for modifier in MODIFIERS if modifier.is_on(self.conf)]
        logger.debug(modifiers)

        nr_unfiltered = len(self.edges)
        for modifier in modifiers:
            modifier.modify(self)

        logger.debug(f'{nr_unfiltered-len(self.edges)} edges removed')