import re
from data.scrapers import Scraper, NoCommentsWarning, UnknownStructureWarning
from datetime import datetime
from collections import defaultdict
import logging
import data.models as models

logger = logging.getLogger('scraper')


class FAZScraper(Scraper):

    @staticmethod
    def assert_url(url):
        return re.match(r'(https?://)?(www\.)?(m\.)?faz\.net/.*', url)

    @staticmethod
    def prepare_url(url):
        url = url.replace('https://m.', 'https://')
        url, _, _ = url.partition('#')
        return url

    @classmethod
    def _scrape(cls, url):
        query_url = f'{url}?printPagedArticle=true#pageIndex_2'
        bs = Scraper.get_html(query_url)
        article = cls._scrape_article(bs, url)
        comments = cls._scrape_comments(bs)

        return article, comments

    @staticmethod
    def _scrape_author(bs):
        author = bs.select('span.atc-MetaAuthor')

        if author:
            author = author[0].get_text().strip()
        else:
            return None
        return author

    @classmethod
    def _scrape_article(cls, bs, url):
        try:
            article = models.ArticleScraped(
                url=url,
                title=bs.select_one('span.atc-HeadlineEmphasisText').get_text().strip() + ' - ' +
                      bs.select_one('span.atc-HeadlineText').get_text().strip(),
                summary=bs.select_one('p.atc-IntroText').get_text().strip(),
                author=cls._scrape_author(bs),
                text='\n\n'.join([e.get_text().strip() for e in bs.select('div.atc-Text p')]),
                published_time=datetime.strptime(bs.select_one('time.atc-MetaTime')['title'], '%d.%m.%Y %H:%M Uhr'),
                scraper=str(cls)
            )
        except IndexError:
            raise UnknownStructureWarning(f'Article structure unknown at {url}')
        return article

    @classmethod
    def _scrape_comments(cls, bs):
        clean_url = bs.select_one('[data-customsharelink]')['data-customsharelink']

        page = 1
        comments = []
        MAX_PAGE = 100
        while True:
            cbs = Scraper.get_html(
                f'{clean_url}?ot=de.faz.ArticleCommentsElement.comments.ajax.ot&action=commentList&page={page}&onlyTopArguments=false')
            if not cbs or len(cbs) == 0:
                break

            for comment_bs in cbs.select('li.lst-Comments_Item-level1'):
                comment = cls._parse_comment(comment_bs.select_one('div.lst-Comments_CommentTextContainer'))
                comments.append(comment)
                for reply_bs in comment_bs.select('li.lst-Comments_Item-level2'):
                    reply = cls._parse_comment(reply_bs.select_one('div.lst-Comments_CommentTextContainer'),
                                               parent_id=comment.comment_id)
                    comments.append(reply)

            page = cbs.select_one('[data-next-page-count]')
            if not page:
                break
            page = page.get('data-next-page-count', None)
            if not page or int(page) > MAX_PAGE:
                break

        return comments

    @classmethod
    def _parse_comment(cls, c, parent_id=None):
        text = ' '.join([t.get_text()
                         for t in c.select('p.lst-Comments_CommentTitle, p.lst-Comments_CommentText')])
        author = c.select_one('a[data-author-name]')
        username = author['data-author-name']
        user_id = author['data-author-login']
        comment_id = c.select_one('ul[data-content-id]')['data-content-id']
        recommended = int(c.select_one('ul[data-empfehlen-value]')['data-empfehlen-value'])
        time = c.select_one('span.lst-Comments_CommentInfoDateText').get_text()

        return models.CommentScraped(
            comment_id=comment_id,
            username=username,
            timestamp=datetime.strptime(time, '%d.%m.%Y - %H:%M'),
            text=text,
            reply_to=parent_id,
            recommended=recommended,
            user_id=user_id
        )


if __name__ == '__main__':
    FAZScraper.test_scraper(
        [
            'https://www.faz.net/aktuell/politik/trumps-praesidentschaft/coronavirus-donald-trump-verhaengt-nationalen-notstand-in-usa-16678564.html#lesermeinungen',
            'https://www.faz.net/aktuell/gesellschaft/menschen/rapper-fler-im-interview-ueber-bushido-und-arafat-abou-chaker-16518885.html',
            'https://www.faz.net/aktuell/technik-motor/sicherheitskontrolle-am-flughafen-frankfurt-blamage-ohne-ende-16514693.html',
            'https://www.faz.net/aktuell/feuilleton/medien/tv-kritik-maischberger-mit-stefan-aust-und-dirk-rossmann-16472805.html',
            'https://www.faz.net/aktuell/rhein-main/drei-mutmassliche-is-anhaenger-in-offenbach-festgenommen-16481443.html',
            'https://www.faz.net/aktuell/politik/inland/bauernproteste-agrarwende-hat-harte-fronten-geschaffen-16505290.html'
        ][:])
