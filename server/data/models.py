from pydantic import BaseModel, AnyHttpUrl
from datetime import datetime
from typing import List, Optional, Union, Tuple
from enum import Enum


class CommentScraped(BaseModel):
    username: str
    comment_id: str
    timestamp: datetime
    text: Union[str, List[str]]
    reply_to: Optional[str]

    # Optional details from FAZ and TAZ
    num_replies: Optional[int]
    user_id: Optional[str]

    # Optional details from SPON
    upvotes: Optional[int]
    downvotes: Optional[int]
    love: Optional[int]

    # Optional details from Welt
    likes: Optional[int]
    recommended: Optional[int]

    # Optional details from ZON
    leseempfehlungen: Optional[int]

    # Optional details from Tagesschau
    title: Optional[str]


class CommentCached(CommentScraped):
    id: int
    article_id: int
    reply_to_id: Optional[int]


class ArticleScraped(BaseModel):
    url: AnyHttpUrl
    title: str
    subtitle: Optional[str]
    summary: Optional[str]
    author: Optional[str]
    text: str
    published_time: datetime
    scrape_time: datetime = datetime.now()
    scraper: str


class CommentedArticle(ArticleScraped):
    comments: List[CommentScraped] = []


class ArticleCached(ArticleScraped):
    id: int
    comments: List[CommentCached] = []


class ScrapeResultStatus(str, Enum):
    OK = 'OK'
    ERROR = 'ERROR'
    NO_COMMENTS = 'NO_COMMENTS'
    NO_SCRAPER = 'NO_SCRAPER'
    SCRAPER_ERROR = 'SCRAPER_ERROR'


class ScrapeResultDetails(BaseModel):
    status: ScrapeResultStatus = ScrapeResultStatus.OK
    error: Optional[str]


class ScrapeResult(BaseModel):
    detail: ScrapeResultDetails = ScrapeResultDetails()
    payload: Optional[CommentedArticle]


class CacheResult(BaseModel):
    detail: ScrapeResultDetails = ScrapeResultDetails()
    payload: Optional[ArticleCached]


class NodeWeightType(str, Enum):
    SIZE = 'SIZE'
    PAGERANK = 'PAGERANK'
    DEGREE_CENTRALITY = 'DEGREE_CENTRALITY'
    RECENCY = 'RECENCY'
    VOTES = 'VOTES'
    TOXICITY = 'TOXICITY'
    MERGE_ID = 'MERGE_ID'
    CLUSTER_ID = 'CLUSTER_ID'


class EdgeWeightType(str, Enum):
    REPLY_TO = 'REPLY_TO'
    SAME_ARTICLE = 'SAME_ARTICLE'
    SIMILARITY = 'SIMILARITY'
    SAME_GROUP = 'SAME_GROUP'
    SAME_COMMENT = 'SAME_COMMENT'
    TEMPORAL = 'TEMPORAL'


class ClusteringAlgorithm(str, Enum):
    GirvanNewman = 'GirvanNewman'
    GreedyModularityCommunities = 'GreedyModularityCommunities'


class ComparatorConfigBase(BaseModel):
    active: bool = True


class SameCommentComparatorConfig(ComparatorConfigBase):
    active: bool = True
    base_weight: float = 1.0
    only_consecutive: bool = True


class SameArticleComparatorConfig(ComparatorConfigBase):
    base_weight: float = 1.0
    only_root: bool = True


class ReplyToComparatorConfig(ComparatorConfigBase):
    base_weight: float = 1.0
    only_root: bool = True


class SimilarityComparatorConfig(ComparatorConfigBase):
    active: bool = False
    base_weight: float = 0.1
    only_root: bool = True
    max_similarity: float = 0.75


class TemporalComparatorConfig(ComparatorConfigBase):
    active: bool = True
    base_weight: float = 1.0
    only_root: bool = True
    max_time: int = 1000


class SizeRankerConfig(ComparatorConfigBase):
    pass


class RecencyRankerConfig(ComparatorConfigBase):
    use_yongest: bool = False


class VotesRankerConfig(ComparatorConfigBase):
    use_upvotes: bool = True
    use_downvotes: bool = True


class PageRankerConfig(ComparatorConfigBase):
    num_iterations: int = 100
    d: float = 0.85
    edge_type: EdgeWeightType = EdgeWeightType.TEMPORAL
    use_power_mode: bool = True


class ToxicityRankerConfig(ComparatorConfigBase):
    active: bool = False
    window_length: int = 125
    whole_comment: bool = True


class CentralityDegreeCalculatorConfig(ComparatorConfigBase):
    pass


class GenericEdgeFilterConfig(ComparatorConfigBase):
    active: bool = False
    threshold: float = 0.13
    smaller_as: bool = False
    edge_type: EdgeWeightType = EdgeWeightType.REPLY_TO


class SimilarityEdgeFilterConfig(ComparatorConfigBase):
    active: bool = False
    threshold: float = 0.3
    smaller_as: bool = False


class ReplyToEdgeFilterConfig(ComparatorConfigBase):
    active: bool = False
    threshold: float = 0.5
    smaller_as: bool = False


class SameCommentEdgeFilterConfig(ComparatorConfigBase):
    active: bool = False
    threshold: float = 0.5
    smaller_as: bool = False


class SameArticleEdgeFilterConfig(ComparatorConfigBase):
    active: bool = False
    threshold: float = 0.5
    smaller_as: bool = False


class SameGroupEdgeFilterConfig(ComparatorConfigBase):
    active: bool = False
    threshold: float = 0.5
    smaller_as: bool = False


class TemporalEdgeFilterConfig(ComparatorConfigBase):
    active: bool = False
    threshold: float = 0.5
    smaller_as: bool = False


class OrEdgeFilterConfig(ComparatorConfigBase):
    active: bool = False
    reply_to_threshold: float = 0.5
    same_comment_threshold: float = 0.5
    same_article_threshold: float = -0.5
    similarity_threshold: float = -0.5
    same_group_threshold: float = -0.5
    temporal_threshold: float = 0.5


class GenericBottomEdgeFilterConfig(ComparatorConfigBase):
    active: bool = False
    top_edges: int = 2
    descending_order: bool = True
    edge_type: EdgeWeightType = EdgeWeightType.REPLY_TO


class BottomSimilarityEdgeFilterConfig(ComparatorConfigBase):
    active: bool = False
    top_edges: int = 5
    descending_order: bool = True


class BottomReplyToEdgeFilterConfig(ComparatorConfigBase):
    active: bool = False
    top_edges: int = 100
    descending_order: bool = True


class BottomTemporalEdgeFilterConfig(ComparatorConfigBase):
    active: bool = False
    top_edges: int = 100
    descending_order: bool = True


class BottomSameCommentFilterConfig(ComparatorConfigBase):
    active: bool = False
    top_edges: int = 100
    descending_order: bool = True


class BottomSameArticleEdgeFilterConfig(ComparatorConfigBase):
    active: bool = False
    top_edges: int = 100
    descending_order: bool = True


class BottomSameGroupEdgeFilterConfig(ComparatorConfigBase):
    active: bool = False
    top_edges: int = 100
    descending_order: bool = True


class GenericNodeWeightFilterConfig(ComparatorConfigBase):
    active: bool = False
    strict: bool = False
    threshold: int = 2
    smaller_as: bool = False
    node_weight_type: NodeWeightType = NodeWeightType.DEGREE_CENTRALITY


class SizeFilterConfig(ComparatorConfigBase):
    active: bool = False
    strict: bool = False
    threshold: int = 1
    smaller_as: bool = False


class PageRankFilterConfig(ComparatorConfigBase):
    active: bool = False
    strict: bool = False
    threshold: int = 1
    smaller_as: bool = False


class DegreeCentralityFilterConfig(ComparatorConfigBase):
    active: bool = False
    strict: bool = False
    threshold: int = 1
    smaller_as: bool = False


class RecencyFilterConfig(ComparatorConfigBase):
    active: bool = False
    strict: bool = False
    threshold: int = 1
    smaller_as: bool = False


class VotesFilterConfig(ComparatorConfigBase):
    strict: bool = False
    threshold: int = 2
    smaller_as: bool = False


class ToxicityFilterConfig(ComparatorConfigBase):
    active: bool = False
    strict: bool = False
    threshold: float = 0.5
    smaller_as: bool = True


class GenericNodeWeightBottomFilterConfig(ComparatorConfigBase):
    active: bool = False
    strict: bool = False
    top_k: int = 5
    descending_order: bool = True
    node_weight_type: NodeWeightType = NodeWeightType.DEGREE_CENTRALITY


class SizeBottomFilterConfig(ComparatorConfigBase):
    active: bool = False
    strict: bool = False
    top_k: int = 5
    descending_order: bool = True


class PageRankBottomFilterConfig(ComparatorConfigBase):
    strict: bool = True
    top_k: int = 200
    descending_order: bool = True


class DegreeCentralityBottomFilterConfig(ComparatorConfigBase):
    active: bool = False
    strict: bool = False
    top_k: int = 5
    descending_order: bool = True


class RecencyBottomFilterConfig(ComparatorConfigBase):
    active: bool = False
    strict: bool = False
    top_k: int = 5
    descending_order: bool = True


class VotesBottomFilterConfig(ComparatorConfigBase):
    active: bool = False
    strict: bool = False
    top_k: int = 50
    descending_order: bool = True


class ToxicityBottomFilterConfig(ComparatorConfigBase):
    active: bool = False
    strict: bool = False
    top_k: int = 500
    descending_order: bool = True


class GenericNodeMergerConfig(ComparatorConfigBase):
    active: bool = False
    threshold: float = 0.5
    smaller_as: bool = False
    edge_weight_type: EdgeWeightType = EdgeWeightType.SAME_COMMENT


class SimilarityNodeMergerConfig(ComparatorConfigBase):
    threshold: float = 0.11
    smaller_as: bool = False


class ReplyToNodeMergerConfig(ComparatorConfigBase):
    threshold: float = 0.5
    smaller_as: bool = False


class SameCommentNodeMergerConfig(ComparatorConfigBase):
    active: bool = False
    threshold: float = 0.5
    smaller_as: bool = False


class SameArticleNodeMergerConfig(ComparatorConfigBase):
    active: bool = False
    threshold: float = 0.5
    smaller_as: bool = False


class SameGroupNodeMergerConfig(ComparatorConfigBase):
    active: bool = False
    threshold: float = 0.5
    smaller_as: bool = False


class TemporalNodeMergerConfig(ComparatorConfigBase):
    active: bool = False
    threshold: float = 0.12
    smaller_as: bool = False


class MultiNodeMergerConfig(ComparatorConfigBase):
    active: bool = False
    reply_to_threshold: float = 0.5
    same_comment_threshold: float = 0.5
    same_article_threshold: float = -0.5
    similarity_threshold: float = -0.5
    same_group_threshold: float = -0.5
    temporal_threshold: float = -0.5
    smaller_as: bool = False
    conj_or: bool = True


class GenericClustererConfig(ComparatorConfigBase):
    active: bool = False
    edge_weight_type: EdgeWeightType = EdgeWeightType.SAME_COMMENT
    algorithm: ClusteringAlgorithm = ClusteringAlgorithm.GirvanNewman


class SimilarityClustererConfig(ComparatorConfigBase):
    active: bool = False
    algorithm: ClusteringAlgorithm = ClusteringAlgorithm.GirvanNewman


class ReplyToClustererConfig(ComparatorConfigBase):
    active: bool = False
    algorithm: ClusteringAlgorithm = ClusteringAlgorithm.GirvanNewman


class SameCommentClustererConfig(ComparatorConfigBase):
    active: bool = False
    algorithm: ClusteringAlgorithm = ClusteringAlgorithm.GirvanNewman


class SameArticleClustererConfig(ComparatorConfigBase):
    active: bool = False
    algorithm: ClusteringAlgorithm = ClusteringAlgorithm.GirvanNewman


class SameGroupClustererConfig(ComparatorConfigBase):
    active: bool = False
    algorithm: ClusteringAlgorithm = ClusteringAlgorithm.GirvanNewman


class TemporalClustererConfig(ComparatorConfigBase):
    active: bool = False
    algorithm: ClusteringAlgorithm = ClusteringAlgorithm.GirvanNewman


class MultiEdgeTypeClustererConfig(ComparatorConfigBase):
    active: bool = False
    use_reply_to: bool = True
    use_same_comment: bool = True
    use_same_article: bool = False
    use_similarity: bool = False
    use_same_group: bool = False
    use_temporal: bool = False
    algorithm: ClusteringAlgorithm = ClusteringAlgorithm.GirvanNewman


class GenericSingleEdgeAdderConfig(ComparatorConfigBase):
    base_weight: float = 0.1
    edge_weight_type: EdgeWeightType = EdgeWeightType.TEMPORAL
    node_weight_type: NodeWeightType = NodeWeightType.RECENCY


class GraphConfig(BaseModel):
    SameCommentComparator: Optional[SameCommentComparatorConfig]
    SameCommentComparator: Optional[SameCommentComparatorConfig]
    SameArticleComparator: Optional[SameArticleComparatorConfig]
    ReplyToComparator: Optional[ReplyToComparatorConfig]
    SimilarityComparator: Optional[SimilarityComparatorConfig]
    TemporalComparator: Optional[TemporalComparatorConfig]
    SizeRanker: Optional[SizeRankerConfig]
    RecencyRanker: Optional[RecencyRankerConfig]
    VotesRanker: Optional[VotesRankerConfig]
    PageRanker: Optional[PageRankerConfig]
    ToxicityRanker: Optional[ToxicityRankerConfig]
    CentralityDegreeCalculator: Optional[CentralityDegreeCalculatorConfig]
    SimilarityEdgeFilter: Optional[SimilarityEdgeFilterConfig]
    ReplyToEdgeFilter: Optional[ReplyToEdgeFilterConfig]
    SameCommentEdgeFilter: Optional[SameCommentEdgeFilterConfig]
    SameArticleEdgeFilter: Optional[SameArticleEdgeFilterConfig]
    SameGroupEdgeFilter: Optional[SameGroupEdgeFilterConfig]
    TemporalEdgeFilter: Optional[TemporalEdgeFilterConfig]
    OrEdgeFilter: Optional[OrEdgeFilterConfig]
    GenericBottomEdgeFilter: Optional[GenericBottomEdgeFilterConfig]
    BottomSimilarityEdgeFilter: Optional[BottomSimilarityEdgeFilterConfig]
    BottomReplyToEdgeFilter: Optional[BottomReplyToEdgeFilterConfig]
    BottomTemporalEdgeFilter: Optional[BottomTemporalEdgeFilterConfig]
    BottomSameCommentFilter: Optional[BottomSameCommentFilterConfig]
    BottomSameArticleEdgeFilter: Optional[BottomSameArticleEdgeFilterConfig]
    BottomSameGroupEdgeFilter: Optional[BottomSameGroupEdgeFilterConfig]
    GenericNodeWeightFilter: Optional[GenericNodeWeightFilterConfig]
    SizeFilter: Optional[SizeFilterConfig]
    PageRankFilter: Optional[PageRankFilterConfig]
    DegreeCentralityFilter: Optional[DegreeCentralityFilterConfig]
    RecencyFilter: Optional[RecencyFilterConfig]
    VotesFilter: Optional[VotesFilterConfig]
    ToxicityFilter: Optional[ToxicityFilterConfig]
    GenericNodeWeightBottomFilter: Optional[GenericNodeWeightBottomFilterConfig]
    SizeBottomFilter: Optional[SizeBottomFilterConfig]
    PageRankBottomFilter: Optional[PageRankBottomFilterConfig]
    DegreeCentralityBottomFilter: Optional[DegreeCentralityBottomFilterConfig]
    RecencyBottomFilter: Optional[RecencyBottomFilterConfig]
    VotesBottomFilter: Optional[VotesBottomFilterConfig]
    ToxicityBottomFilter: Optional[ToxicityBottomFilterConfig]
    GenericNodeMerger: Optional[GenericNodeMergerConfig]
    SimilarityNodeMerger: Optional[SimilarityNodeMergerConfig]
    ReplyToNodeMerger: Optional[ReplyToNodeMergerConfig]
    SameCommentNodeMerger: Optional[SameCommentNodeMergerConfig]
    SameArticleNodeMerger: Optional[SameArticleNodeMergerConfig]
    SameGroupNodeMerger: Optional[SameGroupNodeMergerConfig]
    TemporalNodeMerger: Optional[TemporalNodeMergerConfig]
    MultiNodeMerger: Optional[MultiNodeMergerConfig]
    GenericClusterer: Optional[GenericClustererConfig]
    SimilarityClusterer: Optional[SimilarityClustererConfig]
    ReplyToClusterer: Optional[ReplyToClustererConfig]
    SameCommentClusterer: Optional[SameCommentClustererConfig]
    SameArticleClusterer: Optional[SameArticleClustererConfig]
    SameGroupClusterer: Optional[SameGroupClustererConfig]
    TemporalClusterer: Optional[TemporalClustererConfig]
    MultiEdgeTypeClusterer: Optional[MultiEdgeTypeClustererConfig]
    GenericSingleEdgeAdder: Optional[GenericSingleEdgeAdderConfig]


class SplitWeights(BaseModel):
    # the length of the split
    SIZE: Optional[float]
    # the page rank value for the split / node
    PAGERANK: Optional[float]
    # the degree centrality value for the split / node
    DEGREE_CENTRALITY: Optional[float]
    # the distance (in seconds) to global comparable time (e.g. youngest comment)
    RECENCY: Optional[float]
    # the number of votes for the comment
    VOTES: Optional[float]
    # the toxicity of the comment
    TOXICITY: Optional[float]
    # id of merge group
    MERGE_ID: Optional[float]
    # id of cluster group
    CLUSTER_ID: Optional[float]

    def __getitem__(self, item):
        # return self.__root__[item]
        try:
            return self.dict()[item]
        # hacky fallback
        except KeyError:
            return self.dict()[str(item).split('.')[1]]


class Split(BaseModel):
    # first character of the sentence
    s: int
    # last character of the sentence
    e: int
    # weight / size of split
    wgts: SplitWeights


class SplitComment(BaseModel):
    # database ID of the comment
    id: int
    # ID of the cluster the comment belongs to
    grp_id: Optional[int]
    # List of sentences (splits) the comment is comprised of
    splits: List[Split]


class EdgeWeights(BaseModel):
    # is one comment the reply to the other comment?
    REPLY_TO: Optional[float]
    # belong the two splits to the same article?
    SAME_ARTICLE: Optional[float]
    # cosine similarity between comments
    SIMILARITY: Optional[float]
    # belong the two splits to the same group?
    SAME_GROUP: Optional[float]
    # belong the two splits to the same comment?
    SAME_COMMENT: Optional[float]
    # distance in seconds between comments
    TEMPORAL: Optional[float]

    # this method allows dictionary access, e.g. edge.wgts["reply_to"]
    def __getitem__(self, item):
        # https://pydantic-docs.helpmanual.io/usage/models/
        # return self.__dict__[item]
        try:
            return self.dict()[item]
        # hacky fallback
        except KeyError:
            return self.dict()[str(item).split('.')[1]]

    def __setitem__(self, key, value):
        if key == "REPLY_TO":
            self.REPLY_TO = value
        if key == "SAME_ARTICLE":
            self.SAME_ARTICLE = value
        if key == "SIMILARITY":
            self.SIMILARITY = value
        if key == "SAME_GROUP":
            self.SAME_GROUP = value
        if key == "SAME_COMMENT":
            self.SAME_COMMENT = value
        if key == "TEMPORAL":
            self.TEMPORAL = value


class Edge(BaseModel):
    src: Tuple[int, int]  # first is index of comment, second is index of sentence within comment
    tgt: Tuple[int, int]  # first is index of comment, second is index of sentence within comment
    wgts: EdgeWeights


class Graph(BaseModel):
    article_ids: Optional[List[int]]
    graph_id: Optional[int]

    comments: List[SplitComment]
    id2idx: dict
    edges: List[Edge]
