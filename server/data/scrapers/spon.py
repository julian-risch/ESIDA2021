import re
import json
import requests
from requests.exceptions import HTTPError
from data.scrapers import Scraper
from datetime import datetime, timedelta
import logging
import data.models as models

logger = logging.getLogger('scraper')


class SPONScraper(Scraper):
    @staticmethod
    def assert_url(url):
        return re.match(r'(https?://)?(www\.)?spiegel\.de/.*', url)

    @classmethod
    def _scrape(cls, url):
        bs = Scraper.get_html(url)

        article = cls._scrape_article(bs, url)
        try:
            talk = json.loads(bs.select('div[data-component="Talk"]')[0].get('data-settings'))
            comments = cls._scrape_comments(talk)
        except IndexError:
            raise UserWarning('No Comments found!')
        return article, comments

    @classmethod
    def _scrape_author(cls, bs):
        authors = bs.select('main > article > header div > a')

        if authors:
            author = ', '.join([a.get('title') for a in authors])
        else:
            author = bs.select('meta[name="author"]')[0].get('content').replace(', DER SPIEGEL', '')

        if not author:
            logger.debug('WARN: no author found!')
            return None

        return author

    @classmethod
    def _scrape_article(cls, bs, url):
        header = bs.select('main > article > header')[0]
        summary = header.select('div.leading-loose')
        if summary:
            summary = summary[0].get_text().strip()
        else:
            summary = None
        try:
            article = models.ArticleBase(
                url=url,
                title=' - '.join(reversed([span.get_text().strip() for span in header.select('h2>span')])),
                summary=summary,
                author=cls._scrape_author(bs),
                text='\n\n'.join([e.get_text().strip() for e in bs.select('main>article section p')]),
                published_time=datetime.strptime(bs.select('time.timeformat')[0]['datetime'], '%Y-%m-%d %H:%M:%S'),
                scraper=str(cls)
            )
        except IndexError:
            raise UserWarning("Article Layout not known!")

        return article

    @classmethod
    def _scrape_comments(cls, talk):
        asset_id = talk['articleId']
        base_url = talk['baseURL']

        comments = []

        def flatten(response, parent):
            nodes = response['nodes']
            for n in nodes:
                actions = {action['__typename']: action['count'] for action in n['action_summaries']}
                cid = n['id']
                if n['user'] is not None and n['body'] is not None:
                    comments.append(
                        models.CommentBase(
                            comment_id=cid,
                            username=n['user']['username'],
                            user_id=n['user']['id'],
                            timestamp=datetime.strptime(n['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                            text=n['body'],
                            reply_to=parent,
                            upvotes=actions.get('UpvoteActionSummary', 0),
                            downvotes=actions.get('DownvoteActionSummary', 0),
                            love=actions.get('LoveActionSummary', 0)))
                if 'replies' in n:
                    flatten(n['replies'], parent=cid)

            if response.get('hasNextPage', False):
                cursor = response['endCursor']
                res = cls._load_comments(base_url, asset_id, cursor=cursor, parent_id=parent)
                logger.debug(f'       > cursor: {cursor} | cnt: {len(comments)}', None)
                flatten(res, parent=parent)

        init_response = cls._load_comments(base_url, asset_id)
        flatten(init_response, parent=None)

        return comments

    @classmethod
    def _load_comments(cls, base_url, asset_id, cursor=None, parent_id=None):
        if cursor is None:
            query = {
                "query": "query CoralEmbedStream_Embed($assetId: ID, $assetUrl: String, $commentId: ID!, $hasComment: Boolean!, $excludeIgnored: Boolean, $sortBy: SORT_COMMENTS_BY!, $sortOrder: SORT_ORDER!) {\n  me {\n    id\n    state {\n      status {\n        username {\n          status\n          __typename\n        }\n        banned {\n          status\n          __typename\n        }\n        alwaysPremod {\n          status\n          __typename\n        }\n        suspension {\n          until\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  asset(id: $assetId, url: $assetUrl) {\n    ...CoralEmbedStream_Configure_asset\n    ...CoralEmbedStream_Stream_asset\n    ...CoralEmbedStream_AutomaticAssetClosure_asset\n    __typename\n  }\n  ...CoralEmbedStream_Stream_root\n  ...CoralEmbedStream_Configure_root\n}\n\nfragment CoralEmbedStream_Stream_root on RootQuery {\n  me {\n    state {\n      status {\n        username {\n          status\n          __typename\n        }\n        banned {\n          status\n          __typename\n        }\n        alwaysPremod {\n          status\n          __typename\n        }\n        suspension {\n          until\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    ignoredUsers {\n      id\n      __typename\n    }\n    role\n    __typename\n  }\n  settings {\n    organizationName\n    __typename\n  }\n  ...TalkSlot_StreamTabPanes_root\n  ...TalkSlot_StreamFilter_root\n  ...TalkSlot_Stream_root\n  ...CoralEmbedStream_Comment_root\n  __typename\n}\n\nfragment CoralEmbedStream_Comment_root on RootQuery {\n  me {\n    ignoredUsers {\n      id\n      __typename\n    }\n    __typename\n  }\n  ...TalkSlot_CommentInfoBar_root\n  ...TalkSlot_CommentAuthorName_root\n  ...TalkEmbedStream_DraftArea_root\n  ...TalkEmbedStream_DraftArea_root\n  __typename\n}\n\nfragment TalkEmbedStream_DraftArea_root on RootQuery {\n  __typename\n}\n\nfragment CoralEmbedStream_Stream_asset on Asset {\n  comment(id: $commentId) @include(if: $hasComment) {\n    ...CoralEmbedStream_Stream_comment\n    parent {\n      ...CoralEmbedStream_Stream_singleComment\n      parent {\n        ...CoralEmbedStream_Stream_singleComment\n        parent {\n          ...CoralEmbedStream_Stream_singleComment\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  id\n  title\n  url\n  isClosed\n  created_at\n  settings {\n    moderation\n    infoBoxEnable\n    infoBoxContent\n    premodLinksEnable\n    questionBoxEnable\n    questionBoxContent\n    questionBoxIcon\n    closedTimeout\n    closedMessage\n    disableCommenting\n    disableCommentingMessage\n    charCountEnable\n    charCount\n    requireEmailConfirmation\n    __typename\n  }\n  totalCommentCount @skip(if: $hasComment)\n  comments(query: {limit: 10, excludeIgnored: $excludeIgnored, sortOrder: $sortOrder, sortBy: $sortBy}) @skip(if: $hasComment) {\n    nodes {\n      ...CoralEmbedStream_Stream_comment\n      __typename\n    }\n    hasNextPage\n    startCursor\n    endCursor\n    __typename\n  }\n  ...TalkSlot_StreamTabsPrepend_asset\n  ...TalkSlot_StreamTabPanes_asset\n  ...TalkSlot_StreamFilter_asset\n  ...CoralEmbedStream_Comment_asset\n  __typename\n}\n\nfragment CoralEmbedStream_Comment_asset on Asset {\n  __typename\n  id\n  ...TalkSlot_CommentInfoBar_asset\n  ...TalkSlot_CommentActions_asset\n  ...TalkSlot_CommentReactions_asset\n  ...TalkSlot_CommentAuthorName_asset\n}\n\nfragment CoralEmbedStream_Stream_comment on Comment {\n  id\n  status\n  user {\n    id\n    __typename\n  }\n  ...CoralEmbedStream_Comment_comment\n  __typename\n}\n\nfragment CoralEmbedStream_Comment_comment on Comment {\n  ...CoralEmbedStream_Comment_SingleComment\n  replies(query: {limit: 3, excludeIgnored: $excludeIgnored}) {\n    nodes {\n      ...CoralEmbedStream_Comment_SingleComment\n      replies(query: {limit: 3, excludeIgnored: $excludeIgnored}) {\n        nodes {\n          ...CoralEmbedStream_Comment_SingleComment\n          replies(query: {limit: 3, excludeIgnored: $excludeIgnored}) {\n            nodes {\n              ...CoralEmbedStream_Comment_SingleComment\n              __typename\n            }\n            hasNextPage\n            startCursor\n            endCursor\n            __typename\n          }\n          __typename\n        }\n        hasNextPage\n        startCursor\n        endCursor\n        __typename\n      }\n      __typename\n    }\n    hasNextPage\n    startCursor\n    endCursor\n    __typename\n  }\n  __typename\n}\n\nfragment CoralEmbedStream_Comment_SingleComment on Comment {\n  id\n  body\n  created_at\n  status\n  replyCount\n  tags {\n    tag {\n      name\n      __typename\n    }\n    __typename\n  }\n  user {\n    id\n    username\n    __typename\n  }\n  status_history {\n    type\n    __typename\n  }\n  action_summaries {\n    __typename\n    count\n    current_user {\n      id\n      __typename\n    }\n  }\n  editing {\n    edited\n    editableUntil\n    __typename\n  }\n  ...TalkSlot_CommentInfoBar_comment\n  ...TalkSlot_CommentActions_comment\n  ...TalkSlot_CommentReactions_comment\n  ...TalkSlot_CommentAuthorName_comment\n  ...TalkSlot_CommentContent_comment\n  ...TalkEmbedStream_DraftArea_comment\n  ...TalkEmbedStream_DraftArea_comment\n  __typename\n}\n\nfragment TalkEmbedStream_DraftArea_comment on Comment {\n  __typename\n}\n\nfragment CoralEmbedStream_Stream_singleComment on Comment {\n  id\n  status\n  user {\n    id\n    __typename\n  }\n  ...CoralEmbedStream_Comment_SingleComment\n  __typename\n}\n\nfragment CoralEmbedStream_Configure_root on RootQuery {\n  __typename\n  ...CoralEmbedStream_Settings_root\n}\n\nfragment CoralEmbedStream_Settings_root on RootQuery {\n  __typename\n}\n\nfragment CoralEmbedStream_Configure_asset on Asset {\n  __typename\n  ...CoralEmbedStream_AssetStatusInfo_asset\n  ...CoralEmbedStream_Settings_asset\n}\n\nfragment CoralEmbedStream_AssetStatusInfo_asset on Asset {\n  id\n  closedAt\n  isClosed\n  __typename\n}\n\nfragment CoralEmbedStream_Settings_asset on Asset {\n  id\n  settings {\n    moderation\n    premodLinksEnable\n    questionBoxEnable\n    questionBoxIcon\n    questionBoxContent\n    __typename\n  }\n  __typename\n}\n\nfragment CoralEmbedStream_AutomaticAssetClosure_asset on Asset {\n  id\n  closedAt\n  __typename\n}\n\nfragment TalkSlot_StreamTabPanes_root on RootQuery {\n  ...TalkFeaturedComments_TabPane_root\n  __typename\n}\n\nfragment TalkFeaturedComments_TabPane_root on RootQuery {\n  __typename\n  ...TalkFeaturedComments_Comment_root\n}\n\nfragment TalkFeaturedComments_Comment_root on RootQuery {\n  __typename\n  ...TalkSlot_CommentAuthorName_root\n}\n\nfragment TalkSlot_StreamFilter_root on RootQuery {\n  ...TalkViewingOptions_ViewingOptions_root\n  __typename\n}\n\nfragment TalkViewingOptions_ViewingOptions_root on RootQuery {\n  __typename\n}\n\nfragment TalkSlot_Stream_root on RootQuery {\n  ...Talk_AccountDeletionRequestedSignIn_root\n  __typename\n}\n\nfragment Talk_AccountDeletionRequestedSignIn_root on RootQuery {\n  me {\n    scheduledDeletionDate\n    __typename\n  }\n  __typename\n}\n\nfragment TalkSlot_CommentInfoBar_root on RootQuery {\n  ...TalkModerationActions_root\n  __typename\n}\n\nfragment TalkModerationActions_root on RootQuery {\n  me {\n    id\n    __typename\n  }\n  __typename\n}\n\nfragment TalkSlot_CommentAuthorName_root on RootQuery {\n  ...TalkAuthorMenu_AuthorName_root\n  __typename\n}\n\nfragment TalkAuthorMenu_AuthorName_root on RootQuery {\n  __typename\n  ...TalkSlot_AuthorMenuActions_root\n}\n\nfragment TalkSlot_StreamTabsPrepend_asset on Asset {\n  ...TalkFeaturedComments_Tab_asset\n  __typename\n}\n\nfragment TalkFeaturedComments_Tab_asset on Asset {\n  featuredCommentsCount: totalCommentCount(tags: [\"FEATURED\"]) @skip(if: $hasComment)\n  __typename\n}\n\nfragment TalkSlot_StreamTabPanes_asset on Asset {\n  ...TalkFeaturedComments_TabPane_asset\n  __typename\n}\n\nfragment TalkFeaturedComments_TabPane_asset on Asset {\n  id\n  featuredComments: comments(query: {tags: [\"FEATURED\"], sortOrder: $sortOrder, sortBy: $sortBy, excludeIgnored: $excludeIgnored}, deep: true) @skip(if: $hasComment) {\n    nodes {\n      ...TalkFeaturedComments_Comment_comment\n      __typename\n    }\n    hasNextPage\n    startCursor\n    endCursor\n    __typename\n  }\n  ...TalkFeaturedComments_Comment_asset\n  __typename\n}\n\nfragment TalkFeaturedComments_Comment_comment on Comment {\n  id\n  body\n  created_at\n  replyCount\n  tags {\n    tag {\n      name\n      __typename\n    }\n    __typename\n  }\n  user {\n    id\n    username\n    __typename\n  }\n  ...TalkSlot_CommentReactions_comment\n  ...TalkSlot_CommentAuthorName_comment\n  ...TalkSlot_CommentContent_comment\n  __typename\n}\n\nfragment TalkFeaturedComments_Comment_asset on Asset {\n  __typename\n  ...TalkSlot_CommentReactions_asset\n  ...TalkSlot_CommentAuthorName_asset\n}\n\nfragment TalkSlot_StreamFilter_asset on Asset {\n  ...TalkViewingOptions_ViewingOptions_asset\n  __typename\n}\n\nfragment TalkViewingOptions_ViewingOptions_asset on Asset {\n  __typename\n}\n\nfragment TalkSlot_CommentInfoBar_asset on Asset {\n  ...TalkModerationActions_asset\n  __typename\n}\n\nfragment TalkModerationActions_asset on Asset {\n  id\n  __typename\n}\n\nfragment TalkSlot_CommentActions_asset on Asset {\n  ...TalkPermalink_Button_asset\n  __typename\n}\n\nfragment TalkPermalink_Button_asset on Asset {\n  url\n  __typename\n}\n\nfragment TalkSlot_CommentReactions_asset on Asset {\n  ...UpvoteButton_asset\n  ...DownvoteButton_asset\n  ...LoveButton_asset\n  __typename\n}\n\nfragment UpvoteButton_asset on Asset {\n  id\n  __typename\n}\n\nfragment DownvoteButton_asset on Asset {\n  id\n  __typename\n}\n\nfragment LoveButton_asset on Asset {\n  id\n  __typename\n}\n\nfragment TalkSlot_CommentAuthorName_asset on Asset {\n  ...TalkAuthorMenu_AuthorName_asset\n  __typename\n}\n\nfragment TalkAuthorMenu_AuthorName_asset on Asset {\n  __typename\n}\n\nfragment TalkSlot_CommentInfoBar_comment on Comment {\n  ...TalkFeaturedComments_Tag_comment\n  ...TalkModerationActions_comment\n  __typename\n}\n\nfragment TalkFeaturedComments_Tag_comment on Comment {\n  tags {\n    tag {\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment TalkModerationActions_comment on Comment {\n  id\n  status\n  user {\n    id\n    __typename\n  }\n  tags {\n    tag {\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment TalkSlot_CommentActions_comment on Comment {\n  ...TalkPermalink_Button_comment\n  __typename\n}\n\nfragment TalkPermalink_Button_comment on Comment {\n  id\n  __typename\n}\n\nfragment TalkSlot_CommentReactions_comment on Comment {\n  ...UpvoteButton_comment\n  ...DownvoteButton_comment\n  ...LoveButton_comment\n  __typename\n}\n\nfragment UpvoteButton_comment on Comment {\n  id\n  action_summaries {\n    __typename\n    ... on UpvoteActionSummary {\n      count\n      current_user {\n        id\n        __typename\n      }\n      __typename\n    }\n  }\n  __typename\n}\n\nfragment DownvoteButton_comment on Comment {\n  id\n  action_summaries {\n    __typename\n    ... on DownvoteActionSummary {\n      count\n      current_user {\n        id\n        __typename\n      }\n      __typename\n    }\n  }\n  __typename\n}\n\nfragment LoveButton_comment on Comment {\n  id\n  action_summaries {\n    __typename\n    ... on LoveActionSummary {\n      count\n      current_user {\n        id\n        __typename\n      }\n      __typename\n    }\n  }\n  __typename\n}\n\nfragment TalkSlot_CommentAuthorName_comment on Comment {\n  ...TalkAuthorMenu_AuthorName_comment\n  __typename\n}\n\nfragment TalkAuthorMenu_AuthorName_comment on Comment {\n  __typename\n  id\n  user {\n    username\n    __typename\n  }\n  ...TalkSlot_AuthorMenuInfos_comment\n  ...TalkSlot_AuthorMenuActions_comment\n}\n\nfragment TalkSlot_CommentContent_comment on Comment {\n  ...TalkPluginCommentContent_comment\n  __typename\n}\n\nfragment TalkPluginCommentContent_comment on Comment {\n  body\n  __typename\n}\n\nfragment TalkSlot_AuthorMenuActions_root on RootQuery {\n  ...TalkIgnoreUser_IgnoreUserAction_root\n  __typename\n}\n\nfragment TalkIgnoreUser_IgnoreUserAction_root on RootQuery {\n  me {\n    id\n    __typename\n  }\n  __typename\n}\n\nfragment TalkSlot_AuthorMenuInfos_comment on Comment {\n  ...TalkMemberSince_MemberSinceInfo_comment\n  __typename\n}\n\nfragment TalkMemberSince_MemberSinceInfo_comment on Comment {\n  user {\n    username\n    created_at\n    __typename\n  }\n  __typename\n}\n\nfragment TalkSlot_AuthorMenuActions_comment on Comment {\n  ...TalkIgnoreUser_IgnoreUserAction_comment\n  __typename\n}\n\nfragment TalkIgnoreUser_IgnoreUserAction_comment on Comment {\n  user {\n    id\n    __typename\n  }\n  ...TalkIgnoreUser_IgnoreUserConfirmation_comment\n  __typename\n}\n\nfragment TalkIgnoreUser_IgnoreUserConfirmation_comment on Comment {\n  user {\n    id\n    username\n    __typename\n  }\n  __typename\n}\n",
                "variables": {
                    "assetId": asset_id,
                    "assetUrl": "",
                    "commentId": "",
                    "hasComment": False,
                    "excludeIgnored": False,
                    "sortBy": "CREATED_AT",
                    "sortOrder": "DESC"
                },
                "operationName": "CoralEmbedStream_Embed"
            }
        elif parent_id is None:
            query = {
                "query": "query CoralEmbedStream_LoadMoreComments($limit: Int = 5, $cursor: Cursor, $parent_id: ID, $asset_id: ID, $sortOrder: SORT_ORDER, $sortBy: SORT_COMMENTS_BY = CREATED_AT, $excludeIgnored: Boolean) {\n  comments(query: {limit: $limit, cursor: $cursor, parent_id: $parent_id, asset_id: $asset_id, sortOrder: $sortOrder, sortBy: $sortBy, excludeIgnored: $excludeIgnored}) {\n    nodes {\n      ...CoralEmbedStream_Stream_comment\n      __typename\n    }\n    hasNextPage\n    startCursor\n    endCursor\n    __typename\n  }\n}\n\nfragment CoralEmbedStream_Stream_comment on Comment {\n  id\n  status\n  user {\n    id\n    __typename\n  }\n  ...CoralEmbedStream_Comment_comment\n  __typename\n}\n\nfragment CoralEmbedStream_Comment_comment on Comment {\n  ...CoralEmbedStream_Comment_SingleComment\n  replies(query: {limit: 3, excludeIgnored: $excludeIgnored}) {\n    nodes {\n      ...CoralEmbedStream_Comment_SingleComment\n      replies(query: {limit: 3, excludeIgnored: $excludeIgnored}) {\n        nodes {\n          ...CoralEmbedStream_Comment_SingleComment\n          replies(query: {limit: 3, excludeIgnored: $excludeIgnored}) {\n            nodes {\n              ...CoralEmbedStream_Comment_SingleComment\n              __typename\n            }\n            hasNextPage\n            startCursor\n            endCursor\n            __typename\n          }\n          __typename\n        }\n        hasNextPage\n        startCursor\n        endCursor\n        __typename\n      }\n      __typename\n    }\n    hasNextPage\n    startCursor\n    endCursor\n    __typename\n  }\n  __typename\n}\n\nfragment CoralEmbedStream_Comment_SingleComment on Comment {\n  id\n  body\n  created_at\n  status\n  replyCount\n  tags {\n    tag {\n      name\n      __typename\n    }\n    __typename\n  }\n  user {\n    id\n    username\n    __typename\n  }\n  status_history {\n    type\n    __typename\n  }\n  action_summaries {\n    __typename\n    count\n    current_user {\n      id\n      __typename\n    }\n  }\n  editing {\n    edited\n    editableUntil\n    __typename\n  }\n  ...TalkSlot_CommentInfoBar_comment\n  ...TalkSlot_CommentActions_comment\n  ...TalkSlot_CommentReactions_comment\n  ...TalkSlot_CommentAuthorName_comment\n  ...TalkSlot_CommentContent_comment\n  ...TalkEmbedStream_DraftArea_comment\n  ...TalkEmbedStream_DraftArea_comment\n  __typename\n}\n\nfragment TalkEmbedStream_DraftArea_comment on Comment {\n  __typename\n}\n\nfragment TalkSlot_CommentInfoBar_comment on Comment {\n  ...TalkFeaturedComments_Tag_comment\n  ...TalkModerationActions_comment\n  __typename\n}\n\nfragment TalkFeaturedComments_Tag_comment on Comment {\n  tags {\n    tag {\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment TalkModerationActions_comment on Comment {\n  id\n  status\n  user {\n    id\n    __typename\n  }\n  tags {\n    tag {\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment TalkSlot_CommentActions_comment on Comment {\n  ...TalkPermalink_Button_comment\n  __typename\n}\n\nfragment TalkPermalink_Button_comment on Comment {\n  id\n  __typename\n}\n\nfragment TalkSlot_CommentReactions_comment on Comment {\n  ...UpvoteButton_comment\n  ...DownvoteButton_comment\n  ...LoveButton_comment\n  __typename\n}\n\nfragment UpvoteButton_comment on Comment {\n  id\n  action_summaries {\n    __typename\n    ... on UpvoteActionSummary {\n      count\n      current_user {\n        id\n        __typename\n      }\n      __typename\n    }\n  }\n  __typename\n}\n\nfragment DownvoteButton_comment on Comment {\n  id\n  action_summaries {\n    __typename\n    ... on DownvoteActionSummary {\n      count\n      current_user {\n        id\n        __typename\n      }\n      __typename\n    }\n  }\n  __typename\n}\n\nfragment LoveButton_comment on Comment {\n  id\n  action_summaries {\n    __typename\n    ... on LoveActionSummary {\n      count\n      current_user {\n        id\n        __typename\n      }\n      __typename\n    }\n  }\n  __typename\n}\n\nfragment TalkSlot_CommentAuthorName_comment on Comment {\n  ...TalkAuthorMenu_AuthorName_comment\n  __typename\n}\n\nfragment TalkAuthorMenu_AuthorName_comment on Comment {\n  __typename\n  id\n  user {\n    username\n    __typename\n  }\n  ...TalkSlot_AuthorMenuInfos_comment\n  ...TalkSlot_AuthorMenuActions_comment\n}\n\nfragment TalkSlot_CommentContent_comment on Comment {\n  ...TalkPluginCommentContent_comment\n  __typename\n}\n\nfragment TalkPluginCommentContent_comment on Comment {\n  body\n  __typename\n}\n\nfragment TalkSlot_AuthorMenuInfos_comment on Comment {\n  ...TalkMemberSince_MemberSinceInfo_comment\n  __typename\n}\n\nfragment TalkMemberSince_MemberSinceInfo_comment on Comment {\n  user {\n    username\n    created_at\n    __typename\n  }\n  __typename\n}\n\nfragment TalkSlot_AuthorMenuActions_comment on Comment {\n  ...TalkIgnoreUser_IgnoreUserAction_comment\n  __typename\n}\n\nfragment TalkIgnoreUser_IgnoreUserAction_comment on Comment {\n  user {\n    id\n    __typename\n  }\n  ...TalkIgnoreUser_IgnoreUserConfirmation_comment\n  __typename\n}\n\nfragment TalkIgnoreUser_IgnoreUserConfirmation_comment on Comment {\n  user {\n    id\n    username\n    __typename\n  }\n  __typename\n}\n",
                "variables": {
                    "limit": 10,
                    "cursor": cursor,  # "2020-01-10T12:42:25.974Z",
                    "parent_id": None,
                    "asset_id": asset_id,
                    "sortOrder": "DESC",
                    "sortBy": "CREATED_AT",
                    "excludeIgnored": False
                },
                "operationName": "CoralEmbedStream_LoadMoreComments"
            }
        else:
            query = {
                "query": "query CoralEmbedStream_LoadMoreComments($limit: Int = 5, $cursor: Cursor, $parent_id: ID, $asset_id: ID, $sortOrder: SORT_ORDER, $sortBy: SORT_COMMENTS_BY = CREATED_AT, $excludeIgnored: Boolean) {\n  comments(query: {limit: $limit, cursor: $cursor, parent_id: $parent_id, asset_id: $asset_id, sortOrder: $sortOrder, sortBy: $sortBy, excludeIgnored: $excludeIgnored}) {\n    nodes {\n      ...CoralEmbedStream_Stream_comment\n      __typename\n    }\n    hasNextPage\n    startCursor\n    endCursor\n    __typename\n  }\n}\n\nfragment CoralEmbedStream_Stream_comment on Comment {\n  id\n  status\n  user {\n    id\n    __typename\n  }\n  ...CoralEmbedStream_Comment_comment\n  __typename\n}\n\nfragment CoralEmbedStream_Comment_comment on Comment {\n  ...CoralEmbedStream_Comment_SingleComment\n  replies(query: {limit: 3, excludeIgnored: $excludeIgnored}) {\n    nodes {\n      ...CoralEmbedStream_Comment_SingleComment\n      replies(query: {limit: 3, excludeIgnored: $excludeIgnored}) {\n        nodes {\n          ...CoralEmbedStream_Comment_SingleComment\n          replies(query: {limit: 3, excludeIgnored: $excludeIgnored}) {\n            nodes {\n              ...CoralEmbedStream_Comment_SingleComment\n              __typename\n            }\n            hasNextPage\n            startCursor\n            endCursor\n            __typename\n          }\n          __typename\n        }\n        hasNextPage\n        startCursor\n        endCursor\n        __typename\n      }\n      __typename\n    }\n    hasNextPage\n    startCursor\n    endCursor\n    __typename\n  }\n  __typename\n}\n\nfragment CoralEmbedStream_Comment_SingleComment on Comment {\n  id\n  body\n  created_at\n  status\n  replyCount\n  tags {\n    tag {\n      name\n      __typename\n    }\n    __typename\n  }\n  user {\n    id\n    username\n    __typename\n  }\n  status_history {\n    type\n    __typename\n  }\n  action_summaries {\n    __typename\n    count\n    current_user {\n      id\n      __typename\n    }\n  }\n  editing {\n    edited\n    editableUntil\n    __typename\n  }\n  ...TalkSlot_CommentInfoBar_comment\n  ...TalkSlot_CommentActions_comment\n  ...TalkSlot_CommentReactions_comment\n  ...TalkSlot_CommentAuthorName_comment\n  ...TalkSlot_CommentContent_comment\n  ...TalkEmbedStream_DraftArea_comment\n  ...TalkEmbedStream_DraftArea_comment\n  __typename\n}\n\nfragment TalkEmbedStream_DraftArea_comment on Comment {\n  __typename\n}\n\nfragment TalkSlot_CommentInfoBar_comment on Comment {\n  ...TalkFeaturedComments_Tag_comment\n  ...TalkModerationActions_comment\n  __typename\n}\n\nfragment TalkFeaturedComments_Tag_comment on Comment {\n  tags {\n    tag {\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment TalkModerationActions_comment on Comment {\n  id\n  status\n  user {\n    id\n    __typename\n  }\n  tags {\n    tag {\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment TalkSlot_CommentActions_comment on Comment {\n  ...TalkPermalink_Button_comment\n  __typename\n}\n\nfragment TalkPermalink_Button_comment on Comment {\n  id\n  __typename\n}\n\nfragment TalkSlot_CommentReactions_comment on Comment {\n  ...UpvoteButton_comment\n  ...DownvoteButton_comment\n  ...LoveButton_comment\n  __typename\n}\n\nfragment UpvoteButton_comment on Comment {\n  id\n  action_summaries {\n    __typename\n    ... on UpvoteActionSummary {\n      count\n      current_user {\n        id\n        __typename\n      }\n      __typename\n    }\n  }\n  __typename\n}\n\nfragment DownvoteButton_comment on Comment {\n  id\n  action_summaries {\n    __typename\n    ... on DownvoteActionSummary {\n      count\n      current_user {\n        id\n        __typename\n      }\n      __typename\n    }\n  }\n  __typename\n}\n\nfragment LoveButton_comment on Comment {\n  id\n  action_summaries {\n    __typename\n    ... on LoveActionSummary {\n      count\n      current_user {\n        id\n        __typename\n      }\n      __typename\n    }\n  }\n  __typename\n}\n\nfragment TalkSlot_CommentAuthorName_comment on Comment {\n  ...TalkAuthorMenu_AuthorName_comment\n  __typename\n}\n\nfragment TalkAuthorMenu_AuthorName_comment on Comment {\n  __typename\n  id\n  user {\n    username\n    __typename\n  }\n  ...TalkSlot_AuthorMenuInfos_comment\n  ...TalkSlot_AuthorMenuActions_comment\n}\n\nfragment TalkSlot_CommentContent_comment on Comment {\n  ...TalkPluginCommentContent_comment\n  __typename\n}\n\nfragment TalkPluginCommentContent_comment on Comment {\n  body\n  __typename\n}\n\nfragment TalkSlot_AuthorMenuInfos_comment on Comment {\n  ...TalkMemberSince_MemberSinceInfo_comment\n  __typename\n}\n\nfragment TalkMemberSince_MemberSinceInfo_comment on Comment {\n  user {\n    username\n    created_at\n    __typename\n  }\n  __typename\n}\n\nfragment TalkSlot_AuthorMenuActions_comment on Comment {\n  ...TalkIgnoreUser_IgnoreUserAction_comment\n  __typename\n}\n\nfragment TalkIgnoreUser_IgnoreUserAction_comment on Comment {\n  user {\n    id\n    __typename\n  }\n  ...TalkIgnoreUser_IgnoreUserConfirmation_comment\n  __typename\n}\n\nfragment TalkIgnoreUser_IgnoreUserConfirmation_comment on Comment {\n  user {\n    id\n    username\n    __typename\n  }\n  __typename\n}\n",
                "variables": {
                    "limit": 999999,
                    "cursor": cursor,
                    "parent_id": parent_id,
                    "asset_id": asset_id,
                    "sortOrder": "ASC",
                    "excludeIgnored": False
                },
                "operationName": "CoralEmbedStream_LoadMoreComments"
            }

        res = cls.post_json(f'{base_url}api/v1/graph/ql', json.dumps(query),
                            headers={
                                'Content-Type': 'application/json',
                                'Referer': f'{base_url}embed/stream?asset_id={asset_id}'
                            })
        # nodes[{id, body, created_at, replyCount}], hasNextPage, startCursor, endCursor
        try:
            return res['data']['asset']['comments']
        except (KeyError, TypeError):
            try:
                return res['data']['comments']
            except (KeyError, TypeError):
                return None


if __name__ == '__main__':
    SPONScraper.test_scraper(
        [
            'https://www.spiegel.de/panorama/leute/harry-und-meghan-wie-reagieren-die-windsors-auf-den-megxit-a-6c96e057-b722-4e76-85a2-0c260bda2013',
            # enthält kommentare
            'https://www.spiegel.de/politik/ausland/ex-us-geheimdienstchef-mike-flynn-ueber-den-is-wir-waren-zu-dumm-a-1065038.html',
            # old article, 2 authors
            'https://www.spiegel.de/politik/ausland/donald-trump-und-die-ukraine-affaere-die-wichtigsten-fragen-und-antworten-a-1292642.html',
            # 2 author + city
            'https://www.spiegel.de/politik/deutschland/juergen-trittin-das-konzept-volkspartei-ist-tot-a-1293841.html',
            # 2 author
            'https://www.spiegel.de/wirtschaft/unternehmen/arriva-und-brexit-deutsche-bahn-blaest-boersengang-bei-britischer-tochter-ab-a-1292544.html',
            # 2 author, only 1 comment page
            'https://www.spiegel.de/politik/deutschland/zwickau-angela-merkel-gedenkt-nsu-opfern-a-1294773.html',
            # no author
            'https://www.spiegel.de/kultur/kino/james-dean-1931-1955-soll-rolle-in-vietnam-film-finding-jack-uebernehmen-a-1295269.html',
            # no author
            'https://www.spiegel.de/sport/fussball/trainersuche-beim-fc-bayern-was-eine-entscheidung-mit-weitblick-erschwert-a-1294722.html',
            # 1 author
            'https://www.spiegel.de/wissenschaft/mensch/co2-in-produkten-der-konsument-kann-gar-nicht-lesen-kolumne-a-1292254.html',
            # 1 author, kolumne
            'https://www.spiegel.de/kultur/gesellschaft/faschistische-gesundheitspolitik-weniger-dystopie-wagen-kolumne-a-1294924.html',
            # 1 author, kolumne
            'https://www.spiegel.de/politik/deutschland/bodo-ramelow-und-mike-mohring-volksfront-der-vernunft-kommentar-a-1293596.html',
            # 1 author, comment
            'https://www.spiegel.de/netzwelt/web/talk-to-transformer-kuenstliche-intelligenz-schreibt-texte-fertig-a-1295116.html',
            # 1 author
            'https://www.spiegel.de/politik/deutschland/wahlrechtsreform-so-saehe-deutschland-mit-250-wahlkreisen-aus-a-1294162.html',
            # 1 author
        ][0:10])
