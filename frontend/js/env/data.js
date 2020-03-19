import {E, emitter} from "./events.js";

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