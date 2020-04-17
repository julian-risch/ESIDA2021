from pydantic import BaseModel, validator, ValidationError, AnyHttpUrl
from datetime import datetime
from typing import List, Optional, Union, NamedTuple, Tuple, Dict
from enum import Enum, IntEnum


class CommentScraped(BaseModel):
    username: str
    comment_id: str
    timestamp: datetime
    text: Union[str, List[str]]
    reply_to: Optional[str] = None

    # Optional details from FAZ and TAZ
    num_replies: Optional[int] = None
    user_id: Optional[str] = None

    # Optional details from SPON
    upvotes: Optional[int] = None
    downvotes: Optional[int] = None
    love: Optional[int] = None

    # Optional details from Welt
    likes: Optional[int] = None
    recommended: Optional[int] = None

    # Optional details from ZON
    leseempfehlungen: Optional[int] = None

    # Optional details from Tagesschau
    title: Optional[str] = None


class CommentCached(CommentScraped):
    id: int
    article_id: int
    reply_to_id: Optional[int] = None


class ArticleScraped(BaseModel):
    url: AnyHttpUrl
    title: str
    subtitle: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
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
    error: Optional[str] = None


class ScrapeResult(BaseModel):
    detail: ScrapeResultDetails = ScrapeResultDetails()
    payload: Optional[CommentedArticle] = None


class CacheResult(BaseModel):
    detail: ScrapeResultDetails = ScrapeResultDetails()
    payload: Optional[ArticleCached] = None


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


class ComparatorConfig(BaseModel):
    SameCommentComparator: Optional[SameCommentComparatorConfig] = None
    SameArticleComparator: Optional[SameArticleComparatorConfig] = None
    ReplyToComparator: Optional[ReplyToComparatorConfig] = None


class EdgeType(IntEnum):
    REPLY_TO = 0
    SAME_ARTICLE = 1
    SIMILARITY = 2
    SAME_GROUP = 3
    SAME_COMMENT = 4

class NodeType(IntEnum):
    PAGERANK = 0
    RECENCY = 1
    VOTES = 2

class Split(BaseModel):
    # first character of the sentence
    s: int
    # last character of the sentence
    e: int
    # weight / size of split
    wgt: Optional[float]


class SplitComment(BaseModel):
    # database ID of the comment
    id: int
    # ID of the cluster the comment belongs to
    grp_id: Optional[int] = None
    # List of sentences (splits) the comment is comprised of
    splits: List[Split]


class EdgeWeight(Tuple, NamedTuple):
    # edge weight
    wgt: float
    # edge type
    tp: EdgeType
    # short string of comparator used
    comp: str


# this is just a hack because Pydantic doesnt understand NamedTuples
EdgeWeightType = Tuple[float, EdgeType, str]


class NodeWeight(Tuple, NamedTuple):
    # node weight
    wgt: float
    # node weight type
    tp: NodeType
    # short string of modificator used
    mod: str

# this is just a hack because Pydantic doesnt understand NamedTuples
NodeWeightType = Tuple[float, NodeType, str]


class Node(BaseModel):
    id: int
    wgts: List[EdgeWeightType]


class Edge(BaseModel):
    src: List[int]  # first is index of comment, second is index of sentence within comment
    tgt: List[int]  # first is index of comment, second is index of sentence within comment
    wgts: List[EdgeWeightType]


class Graph(BaseModel):
    article_ids: Optional[List[int]] = None
    graph_id: Optional[int] = None

    comments: List[SplitComment]
    id2idx: dict
    edges: List[Edge]
    nodes: List[Node]
