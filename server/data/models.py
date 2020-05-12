from pydantic import BaseModel, AnyHttpUrl
from datetime import datetime
from typing import List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass


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


class ComparatorConfigBase(BaseModel):
    active: bool = True


class SameCommentComparatorConfig(ComparatorConfigBase):
    base_weight: float = None
    only_consecutive: bool = True


class SameArticleComparatorConfig(ComparatorConfigBase):
    base_weight: float = None
    only_root: bool = True


class ReplyToComparatorConfig(ComparatorConfigBase):
    base_weight: float = None
    only_root: bool = True


class SimilarityComparatorConfig(ComparatorConfigBase):
    base_weight: float = 0.1
    only_root: bool = True
    max_similarity: float = 0.5


class TemporalComparatorConfig(ComparatorConfigBase):
    base_weight: float = 0.1
    only_root: bool = True
    max_time: int = 1000


class PageRankerConfig(ComparatorConfigBase):
    num_iterations: int = 100
    d: float = 0.85
    normalize: bool = True


class CentralityDegreeCalculatorConfig(ComparatorConfigBase):
    pass


class BottomSimilarityEdgeFilterConfig(ComparatorConfigBase):
    top_edges: int = 5


class BottomReplyToEdgeFilterConfig(ComparatorConfigBase):
    top_edges: int = 5


class SimilarityEdgeFilterConfig(ComparatorConfigBase):
    threshold: float = 0.7


class GraphConfig(BaseModel):
    SameCommentComparator: Optional[SameCommentComparatorConfig]
    SameArticleComparator: Optional[SameArticleComparatorConfig]
    ReplyToComparator: Optional[ReplyToComparatorConfig]
    SimilarityComparator: Optional[SimilarityComparatorConfig]
    TemporalComparator: Optional[TemporalComparatorConfig]
    PageRanker: Optional[PageRankerConfig]
    CentralityDegreeCalculator: Optional[CentralityDegreeCalculatorConfig]
    BottomReplyToEdgeFilter: Optional[BottomReplyToEdgeFilterConfig]
    BottomSimilarityEdgeFilter: Optional[BottomSimilarityEdgeFilterConfig]
    SimilarityEdgeFilter: Optional[SimilarityEdgeFilterConfig]


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

    def __getitem__(self, item):
        return self.__root__[item]


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
        return self.__dict__[item]


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
