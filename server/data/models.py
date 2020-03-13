from pydantic import BaseModel, validator, ValidationError, AnyHttpUrl
from datetime import datetime
from typing import List, Optional
from enum import Enum
import re


class CommentBase(BaseModel):
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
    child_count: Optional[int] = None

    # Optional details from ZON
    leseempfehlungen: Optional[int] = None

    # Optional details from Tagesschau
    title: Optional[str] = None


class CommentCreate(CommentBase):
    pass


class Comment(CommentBase):
    id: int
    article_id: int

    class Config:
        orm_mode = True


class ArticleBase(BaseModel):
    url: AnyHttpUrl
    title: str
    subtitle: str = None
    summary: str = None
    author: str = None
    text: str
    published_time: datetime
    scrape_time: datetime = datetime.now()
    scraper: str


class ArticleCreate(ArticleBase):
    pass


class Article(ArticleBase):
    id: int
    comments: List[Comment] = []

    class Config:
        orm_mode = True


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
    payload: Article = None
