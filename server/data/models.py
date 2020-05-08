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


class SplitWeights:
    # the length of the split
    size: Optional[float] = None
    # the page rank value for the split / node
    pagerank: Optional[float] = None
    # the degree centrality value for the split / node
    degree_centrality: Optional[float] = None
    # the distance (in seconds) to global comparable time (e.g. youngest comment)
    recency: Optional[float] = None
    # the number of votes for the comment
    votes: Optional[float] = None


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
    grp_id: Optional[int] = None
    # List of sentences (splits) the comment is comprised of
    splits: List[Split]


class EdgeWeights(BaseModel):
    # is one comment the reply to the other comment?
    reply_to: Optional[float]
    # belong the two splits to the same article?
    same_article: Optional[float]
    # cosine similarity between comments
    similarity: Optional[float]
    # belong the two splits to the same group?
    same_group: Optional[float]
    # belong the two splits to the same comment?
    same_comment: Optional[float]
    # distance in seconds between comments
    temporal: Optional[float]


class Edge(BaseModel):
    src: Tuple[int, int]  # first is index of comment, second is index of sentence within comment
    tgt: Tuple[int, int]  # first is index of comment, second is index of sentence within comment
    wgts: EdgeWeights


class Graph(BaseModel):
    article_ids: Optional[List[int]] = None
    graph_id: Optional[int] = None

    comments: List[SplitComment]
    id2idx: dict
    edges: List[Edge]
