import re
from data.scrapers import Scraper, UnknownStructureWarning
from datetime import datetime
import logging
import data.models as models

logger = logging.getLogger('scraper')


class WeltScraper(Scraper):
    @staticmethod
    def assert_url(url):
        return re.match(r'https?://(www\.)?welt\.de/.*', url)

    @classmethod
    def _scrape(cls, url):
        bs = Scraper.get_html(url)
        article = cls._scrape_article(bs, url)
        comments = cls._scrape_comments(url)

        return article, comments

    @classmethod
    def _scrape_article(cls, bs, url):
        article_parts = bs.select('.c-article-text p')
        try:
            article = models.ArticleScraped(
                url=url,
                title=bs.select('.c-headline')[0].get_text().strip(),
                summary=bs.select('.c-summary__intro')[0].get_text().strip(),
                author=cls._scrape_author(bs),
                text='\n\n'.join([e.get_text().strip() for e in article_parts]),
                published_time=datetime.strptime(bs.select('.c-publish-date')[0]['datetime'], '%Y-%m-%dT%H:%M:%S%z'),
                scraper=str(cls)
            )
        except IndexError:
            raise UnknownStructureWarning(f'Scraper {cls} can\'t deal with the article layout for {url}')

        return article

    @classmethod
    def _scrape_author(cls, bs):
        if bs.select('.c-author__by-line a'):
            return bs.select('.c-author__by-line a')[0].get_text().strip()
        elif bs.select('.c-author__by-line'):
            return bs.select('.c-author__by-line')[0].get_text().strip()
        # add more cases to capture author
        else:
            logger.debug('WARN: no author found!')
            return None

    @classmethod
    def _scrape_comments(cls, url):
        comments = {}
        doc_id = re.search(r'/(?:article|plus|live)(\d+)/', url).group(1)
        base_url = f'https://api-co.la.welt.de/api/comments?document-id={doc_id}&sort=NEWEST&limit=100'

        parents = []

        cursor = None
        while True:
            url = base_url
            if cursor:
                url = f'{base_url}&created-cursor={cursor}'
            raw_comments = cls.get_json(url)['comments']

            if raw_comments:
                if raw_comments[-1]['created'] == cursor:
                    break
                cursor = raw_comments[-1]['created']
                for c in raw_comments:
                    comment = cls._parse_comment(c)
                    comments[comment.comment_id] = comment
                    if c['child_count'] > 0:
                        parents.append(comment.comment_id)
            else:
                break

        for parent_id in parents:
            raw_comments = cls.get_json(f'{base_url}&parent-id={parent_id}')['comments']
            for c in raw_comments:
                comment = cls._parse_comment(c)
                comments[comment.comment_id] = comment

        return comments.values()

    @classmethod
    def _parse_comment(cls, e):
        return models.CommentScraped(
            comment_id=e['id'],
            username=e['user']['displayName'],
            timestamp=cls._get_comment_created(e),
            text=e['contents'],
            reply_to=e.get('parentId', None),
            user_id=e['user']['id'],
            likes=e['likes'],
            recommended=e['recommended']
        )

    @staticmethod
    def _get_comment_created(e):
        try:
            return datetime.strptime(e['created'].strip(), '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            return datetime.strptime(e['created'].strip(), '%Y-%m-%dT%H:%M:%S')


if __name__ == '__main__':
    WeltScraper.test_scraper([
        'https://www.welt.de/politik/deutschland/article203182606/Aus-Syrien-Deutschland-muss-mutmassliche-IS-Anhaengerin-zurueckholen.html',
        'https://www.welt.de/politik/deutschland/article203346702/Grundrente-FDP-Chef-Lindner-tadelt-Willkuerrente.html',
        'https://www.welt.de/kultur/kunst-und-architektur/article194890561/Humboldt-Forum-Das-Museum-fuer-innere-Leere-mitten-in-Berlin.html',
        'https://www.welt.de/politik/ausland/plus203109148/Wolfgang-Ischinger-Wir-tun-das-nicht-fuer-Trump-wir-tun-das-fuer-uns.html'

    ])
