import { E, emitter } from "./events.js";


const EDGE_TYPES = Object.freeze({
    REPLY_TO: 0,
    SAME_ARTICLE: 1,
    SIMILARITY: 2,
    SAME_GROUP: 3,
    SAME_COMMENT: 4
});


class DataStore {
    comments = [];
    sources = [];

    constructor() {
        emitter.on(E.RECEIVED_ARTICLE, this.onArticleReceive)
    }

    onArticleReceive(d) {

    }

    addComments(comments) {
        this.comments.push()
    }
}

export { DataStore };