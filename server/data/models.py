from pydantic import BaseModel, validator, ValidationError, AnyHttpUrl
from datetime import datetime
from typing import List, Optional
from enum import Enum
import re


class CommentScraped(BaseModel):
    username: str
    comment_id: str
    timestamp: datetime
    text: str
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


class ArticleScraped(BaseModel):
    url: AnyHttpUrl
    title: str
    subtitle: str = None
    summary: str = None
    author: str = None
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
    error: str = None


class ScrapeResult(BaseModel):
    detail: ScrapeResultDetails = ScrapeResultDetails()
    payload: CommentedArticle = None


class CacheResult(BaseModel):
    detail: ScrapeResultDetails = ScrapeResultDetails()
    payload: ArticleCached = None


class EdgeType(str, Enum):
    CHILD_OF = 'CHILD_OF'
    SAME_ARTICLE = 'SAME_ARTICLE'
    SIMILARITY = 'SIMILARITY'
    SAME_GROUP = 'SAME_GROUP'


class Edge(BaseModel):
    comment_a: int
    comment_b: int
    weight: float
    type: EdgeType
