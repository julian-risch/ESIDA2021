import { emitter, E } from "./env/events.js";
import { data, API_SETTINGS, GRAPH_CONFIG, Article } from "./env/data.js";

const request = (method, url, payload, rawPayload = false) => {
    return new Promise(function (resolve, reject) {
        let xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (this.readyState === 4) {
                if (this.status === 200) {
                    let r = this.responseText;
                    if (this.getResponseHeader("Content-Type") === 'application/json')
                        r = JSON.parse(r);
                    resolve(r);
                } else {
                    reject('FAIL');
                }
            }
        };
        xhttp.open(method, url, true);
        xhttp.setRequestHeader('Accept', 'application/json');
        xhttp.setRequestHeader('Accept', 'text/plain');
        xhttp.send(rawPayload ? payload : JSON.stringify(payload));
    });
};

const GET = (url) =>
    request('GET', url);

const POST = (url, payload, rawPayload = false) =>
    request('POST', url, payload, rawPayload);

/**
 * This should be a 1:1 copy of the API as specified in the openapi.json
 */
const _api = Object.freeze({
    'GET': {
        '/api/platforms/article': (url, overrideCache, ignoreCache) => {
            let query = '/api/platforms/article?';
            query += 'identifier=' + encodeURIComponent(url);
            if (overrideCache)
                query += '&override_cache=true';
            if (ignoreCache)
                query += '&ignore_cache=true';

            return GET(query);
        },
        '/api/platforms/scrape': (url) => {
            let query = '/api/platforms/scrape?';
            query += 'url=' + encodeURIComponent(url);

            return GET(query);
        },
        '/api/ping': () => {
            return GET('/api/ping');
        }
    },
    'POST': {
        '/api/ping/{name}': (name) => {
            let query = `/api/ping/${name}`;
            return POST(query);
        },
        '/api/graph/': (articleIds, urls, overrideCache, ignoreCache, conf) => {
            let query = '/api/graph/';
            let params = [];
            if (overrideCache)
                params.push('override_cache=true');
            if (ignoreCache)
                params.push('ignore_cache=true');
            if (params.length > 0)
                query += '?' + params.join('&');

            return POST(query, {
                article_ids: articleIds,
                urls: urls,
                conf: conf
            });
        }
    }
});

const SCRAPERS = Object.freeze({
    isValidURL: (url) => !!url.match(/^https?:\/\/(www\.)?(zeit|sz|sueddeutsche|faz|spiegel|tagesschau|welt|taz)\.(de|net)\/.*$/i),
    scraper2source: {
        "<class 'data.scrapers.faz.FAZScraper'>": 'faz',
        "<class 'data.scrapers.spon.SPONScraper'>": 'spiegel',
        "<class 'data.scrapers.sz.SZScraper'>": 'sz',
        "<class 'data.scrapers.tagesschau.TagesschauScraper'>": 'tagesschau',
        "<class 'data.scrapers.taz.TAZScraper'>": 'taz',
        "<class 'data.scrapers.welt.WeltScraper'>": 'welt',
        "<class 'data.scrapers.zon.ZONScraper'>": 'zeit'
    },
    CODES: {
        OK: 'OK',
        ERROR: 'ERROR',
        NO_COMMENTS: 'NO_COMMENTS',
        NO_SCRAPER: 'NO_SCRAPER',
        SCRAPER_ERROR: 'SCRAPER_ERROR'
    }
});

class Api {
    constructor() {
        this.isValidScraperUrl = SCRAPERS.isValidURL;
        this._initListeners();
    }

    _initListeners() {
        emitter.on(E.NEW_SOURCE_URL, this.getArticle.bind(this));
        emitter.on(E.GRAPH_REQUESTED, () => {
            this.getGraph(data.getArticleIds());
        });
    }

    getArticle(url) {
        _api.GET["/api/platforms/article"](url).then((d) => {
            if (d.detail.status === SCRAPERS.CODES.OK) {
                let article = new Article(d.payload.url,
                    d.payload.title,
                    d.payload.subtitle,
                    d.payload.summary,
                    d.payload.author,
                    d.payload.text,
                    new Date(d.payload.published_time),
                    new Date(d.payload.scrape_time),
                    SCRAPERS.scraper2source[d.payload.scraper],
                    d.payload.id,
                    d.payload.comments.length);
                emitter.emit(E.RECEIVED_ARTICLE, article);
                emitter.emit(E.RECEIVED_COMMENTS, d.payload.comments)
            } else {
                emitter.emit(E.ARTICLE_FAILED, d);
            }
        }).catch((e) => {
            console.error(e);
            emitter.emit(E.ARTICLE_FAILED, e);
        });
    }

    getGraph(articleIds, conf) {
        if (!conf)
            conf = GRAPH_CONFIG;
        _api.POST["/api/graph/"](articleIds, null,
            API_SETTINGS.GRAPH_OVERRIDE_CACHE,
            API_SETTINGS.GRAPH_IGNORE_CACHE, conf).then(d => {
            emitter.emit(E.GRAPH_RECEIVED, d.graph_id, d.comments, d.id2idx, d.edges);
        }).catch((e) => {
            console.error(e);
            emitter.emit(E.GRAPH_REQUEST_FAILED, e);
        });
    }
}


const API = new Api();

export { API }