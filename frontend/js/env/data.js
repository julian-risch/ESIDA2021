import { E, emitter } from "./events.js";


const EDGE_TYPES = Object.freeze({
    REPLY_TO: 0,
    SAME_ARTICLE: 1,
    SIMILARITY: 2,
    SAME_GROUP: 3,
    SAME_COMMENT: 4
});
const EDGE_TYPES_REV = Object.freeze(Object.fromEntries(
    Object.entries(EDGE_TYPES).map(([k, v]) => [v, k])));

const GRAPH_CONFIG = {
    SameCommentComparator: {
        active: true,
        base_weight: 1.0,
        only_consecutive: true
    },
    SameArticleComparator: {
        active: false,
        base_weight: 1.0,
        only_root: true
    },
    ReplyToComparator: {
        active: true,
        base_weight: 1.0,
        only_root: true
    }
};

const API_SETTINGS = {
    GRAPH_IGNORE_CACHE: true
};

class Article {
    constructor(url, title, subtitle, summary, author, text,
                publishedTime, scrapeTime, scraper, articleId, numComments) {
        this.url = url;
        this.title = title;
        this.subtitle = subtitle;
        this.summary = summary;
        this.author = author;
        this.text = text;
        this.publishedTime = publishedTime;
        this.scrapeTime = scrapeTime;
        this.source = scraper;
        this.articleId = articleId;
        this.numComments = numComments;
    }
}

class DataStore {
    comments = {};
    sources = {};
    id2idx = {};
    edges = [];
    groups = {};

    constructor() {
        emitter.on(E.RECEIVED_ARTICLE, this.onArticleReceive.bind(this));
        emitter.on(E.RECEIVED_COMMENTS, this.onCommentsReceive.bind(this));
        emitter.on(E.GRAPH_RECEIVED, this.onGraphReceive.bind(this));
    }

    onCommentsReceive(comments) {
        comments.forEach(c => {
            this.comments[c.id] = c;
        });
    }

    onArticleReceive(article) {
        this.sources[article.articleId] = article;
    }

    onGraphReceive(graph_id, splitComments, id2idx, edges) {
        this.id2idx = id2idx;
        this.idx2id = Object.fromEntries(Object.entries(id2idx).map(([k, v]) => [v, k]));
        this.edges = edges;
        splitComments.forEach(splitComment => {
            this.comments[splitComment.id].group = splitComment.grp_id;
            if (!(splitComment.grp_id in this.groups)) this.groups[splitComment.grp_id] = [];
            this.groups[splitComment.grp_id].push(splitComment.id);

            let text = this.comments[splitComment.id].text;
            //this.comments[splitComment.id].splits = splitComment.splits.map((split) => text.substr(split.s, split.e));
            this.comments[splitComment.id].splits = splitComment.splits;
        });

        emitter.emit(E.REDRAW);
    }

    getCommentText(commentId, split) {
        let bounds = this.comments[commentId].splits[split];
        return this.comments[commentId].text.substr(bounds.s, bounds.e);
    }

    getArticleIds() {
        return Object.keys(this.sources).map(k => parseInt(k));
    }

}

let data = new DataStore();

export { GRAPH_CONFIG, API_SETTINGS, DataStore, Article, data, EDGE_TYPES, EDGE_TYPES_REV };