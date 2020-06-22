import { LANG, FORMAT_DATE } from './lang.js';
import { EXAMPLE_STORIES } from "./examples.js";
import { emitter, E } from "./events.js"
import { API } from "../api.js";
import { ComExDrawing } from "../drawing/drawing.js";
import { ConfigPanel } from "../drawing/config.js";
import { TimeSlider } from "../drawing/timeslider.js";
import { data } from "./data.js";
import { URI } from "./uri.js";

function nElem({ tag, cls = null, attribs = null, id = null, text = null, children = null }) {
    let elem = document.createElement(tag);
    if (!!text)
        elem.appendChild(document.createTextNode(text));
    if (!!cls)
        if (Array.isArray(cls)) {
            cls.forEach((cls) => elem.classList.add(cls))
        } else if (typeof cls === 'string') {
            elem.classList.add(cls);
        }
    if (!!id)
        elem.id = id;
    if (!!attribs)
        attribs.forEach((attrib) => elem.setAttribute(attrib[0], attrib[1]));

    if (!!children)
        children.forEach((child) => elem.appendChild(child));

    return elem;
}

function getNodes(str) {
    return new DOMParser().parseFromString(str, 'text/html').body.children;
}

function getNode(str) {
    return getNodes(str)[0];
}

Node.prototype.appendChildren = function (nodeList, replace = false) {
    if (replace)
        this.innerHTML = '';
    Array.from(nodeList).forEach(node => this.appendChild(node));
};

Node.prototype.setChild = function (node) {
    this.innerHTML = '';
    this.appendChild(node);
};

const LOADER = `
    <div class="loading">
        <div></div>
        <div></div>
        <div></div>
    </div>`;

class AddSourceModalElements {
    constructor() {
        this.ROOT = document.getElementById('add-source-modal');
        this.CLOSE_BUTTON = document.querySelector('#add-source-modal .close');
        this.URL = document.querySelector('#add-source-modal input');
        this.SUBMIT = document.querySelector('#add-source-modal .button');

        this._initStaticListeners()
    }

    _hide(e) {
        if (!!e)
            e.stopPropagation();
        this.ROOT.style.display = 'none';
    }

    get hide() {
        return this._hide.bind(this);
    }

    _show() {
        // FIXME: remove comment in following line!
        //this.resetURL();
        this.ROOT.style.display = 'block';
    }

    resetURL() {
        this.URL.value = '';
        this.URL.setCustomValidity('');
    }

    get show() {
        return this._show.bind(this);
    }

    get url() {
        return this.URL.value;
    }

    _initStaticListeners() {
        this.ROOT.addEventListener('click', (e) => {
            if (e.target === this.ROOT) {
                e.stopPropagation();
                this._hide();
            }
        });
        this.CLOSE_BUTTON.addEventListener('click', this.hide);
        this.SUBMIT.addEventListener('click', () => {
            if (API.isValidScraperUrl(this.url)) {
                // add new source to list in URL
                let srcs = URI.get_arr('source', []);
                srcs.push(this.url);
                URI.set_val('source', srcs, false);

                // request new data
                emitter.emit(E.NEW_SOURCE_URL, this.url);
                this._hide();
            } else {
                this.URL.setCustomValidity('No source matched.')
            }
        });
    }
}

const SOURCES = {
    faz: {
        icon: 'img/platform_icons/faz.svg',
        logo: 'img/platform_logos/faz.svg',
        name: 'Frankfurter Allgemeine'
    },
    spiegel: {
        icon: 'img/platform_icons/spiegel.png',
        logo: 'img/platform_logos/spiegel.png',
        name: 'Spiegel Online'
    },
    sz: {
        icon: 'img/platform_icons/sz.png',
        logo: 'img/platform_logos/sz.svg',
        name: 'Süddeutsche Zeitung'
    },
    tagesschau: {
        icon: 'img/platform_icons/tagesschau.png',
        logo: 'img/platform_logos/tagesschau.svg',
        name: 'Tagesschau.de'
    },
    taz: {
        icon: 'img/platform_icons/taz.png',
        logo: 'img/platform_logos/taz.svg',
        name: 'TAZ'
    },
    welt: {
        icon: 'img/platform_icons/welt.png',
        logo: 'img/platform_logos/welt.svg',
        name: 'Welt'
    },
    zeit: {
        icon: 'img/platform_icons/zeit.png',
        logo: 'img/platform_logos/zeit.svg',
        name: 'Zeit Online'
    }
};

class SidebarSourceElement {
    constructor(num, openModalFunc, src, url, title, date, comments) {
        this.ROOT = getNode(`
            <div class="source">
                <h1>${LANG.SOURCE.s} ${num}</h1>
                <div class="content">
                
                </div>
            </div>`);
        this.CONTENT = this.ROOT.querySelector('div.content');

        if (!src && !url && !title && !date && !comments) {
            this._initEmpty(openModalFunc);
        } else {
            this.update(src, url, title, date, comments);
        }
    }

    _initEmpty(openModalFunc) {
        let button = getNode('<div class="add">+</div>');
        this.CONTENT.appendChild(button);
        button.addEventListener('click', openModalFunc);
        emitter.on(E.NEW_SOURCE_URL, () => {
            button.innerHTML = LOADER;
        });
        emitter.once(E.RECEIVED_ARTICLE, (d) => {
            this.update(d.source, d.url, d.title, d.publishedTime, d.numComments);
        });
        emitter.on(E.ARTICLE_FAILED, () => {
            button.innerHTML = 'X';
            setTimeout(() => button.innerHTML = '+', 1000);
        });
    }

    update(src, url, title, date, num_comments) {
        let info = getNodes(`
            <div class="platform">
                <img src="${SOURCES[src].icon}" alt="" /> ${SOURCES[src].name}
            </div>
            <h2>
                <a target="_blank" href="${url}">${title}</a>
            </h2>
            <div class="info">
                <time datetime="${FORMAT_DATE["YYYY-mm-dd HH:MM"](date)}">${LANG.DATETIME.s(date)}</time>
                <span class="comments">${num_comments} ${LANG.COMMENTS.s}</span>
            </div>`);
        this.CONTENT.appendChildren(info, true);
    }
}

class SidebarExampleElement {
    constructor() {
        this.ROOT = document.getElementById('example-selection');

        EXAMPLE_STORIES.forEach(
            (story, i) => {
                // <input name="selectors" type="radio" id="example-selection-1" checked>
                // <label for="example-selection-1">Pick Example!</label>
                let id = `example-selection-${i}`;
                let attribs = [['type', 'radio'], ['name', 'example-selection-selectors']];
                if (i === 0)
                    attribs.push(['checked', '']);

                let elem = nElem({ tag: 'input', id: id, attribs: attribs });
                elem.addEventListener('change', () => {
                    console.log(story)
                    emitter.emit(E.EXAMPLE_SELECTED, story);
                });
                this.ROOT.appendChild(elem);

                elem = nElem({ tag: 'label', text: story.title, attribs: [['for', id]] });
                this.ROOT.appendChild(elem);
                return elem;
            })
    }
}

class SidebarElements {
    constructor(openModalFunc) {
        this.openModalFunc = openModalFunc;
        this.ROOT = document.getElementById('sources');
        this.EXAMPLE_PICKER = new SidebarExampleElement();
        this.SOURCES = [];
        this._initListeners();
    }

    _initListeners() {
        emitter.on(E.RECEIVED_ARTICLE, () => {
            this.addEmptySource();
        })
    }

    _addSource(srcElem) {
        this.SOURCES.push(srcElem);
        this.ROOT.appendChild(srcElem.ROOT);
    }

    addSource(src, url, title, date, comments) {
        this._addSource(new SidebarSourceElement(this.SOURCES.length + 1, undefined, src, url, title, date, comments));
    }

    addEmptySource() {
        this._addSource(new SidebarSourceElement(this.SOURCES.length + 1, this.openModalFunc));
    }
}

class CommentSidebarComment {
    constructor(comment) {
        let date = new Date(comment.timestamp);

        this.ROOT = getNode(`<li>
            <div>
                <span>${comment.username}</span> •
                <time datetime="${FORMAT_DATE["YYYY-mm-dd HH:MM"](date)}">${LANG.DATETIME.s(date)}</time>
            </div>
            <p>
                ${comment.text}
            </p>
        </li>`);

        this.ROOT.addEventListener('click', () => {
            emitter.emit(E.COMMENT_SELECTED, comment.id);
        });

        this.isHighlighted = false;
        this.visible = true;
    }

    toggleHighlight(force) {
        this.isHighlighted = (force !== undefined) ? force : !this.isHighlighted;
        this.ROOT.classList.toggle('highlight', this.isHighlighted);
        return this.isHighlighted;
    }

    applyFilter(active) {
        if (active === this.visible) return; // do nothing if nothing changed
        this.visible = active;
        this.ROOT.style.display = active ? 'list-item' : 'none';
    }
}

class CommentSidebar {
    constructor() {
        this.isVisible = false;

        this.ROOT = document.getElementById('comments');
        this.LIST = document.querySelector('#comments > ul');
        this.SIDEBAR_TOGGLE_BUTTON = document.getElementById('comments-toggle');
        this.BUTTON_CLEAR_FILTERS = document.getElementById('comments-filters-clear');
        this.BUTTON_SEARCH = document.querySelector('#comments-filters-search > button');
        this.SEARCH_BOX = document.querySelector('#comments-filters-search > input');
        this.SEARCH_BOX.setAttribute('placeholder', LANG.SEARCH.s + '…')
        this.COUNTER = document.getElementById('comments-filters-counter');

        this.COMMENTS = {};

        this.SIDEBAR_TOGGLE_BUTTON.addEventListener('click', this.toggleShow.bind(this));
        this.SEARCH_BOX.addEventListener('input', this.searchSubmit.bind(this));
        this.BUTTON_SEARCH.addEventListener('click', this.searchSubmit.bind(this));
        this.BUTTON_CLEAR_FILTERS.addEventListener('click', () => emitter.emit(E.CLEAR_SEARCH_FILTER));

        emitter.on(E.DATA_UPDATED_COMMENTS, this.onCommentsReceived.bind(this));
        emitter.on(E.COMMENT_SELECTED, this.onCommentHighlight.bind(this));
        emitter.on(E.FILTERS_UPDATED, this.onFiltersChanged.bind(this));

        this.currentlySelected = null;
    }

    onCommentHighlight(commentId) {
        if (this.currentlySelected !== null) {
            this.COMMENTS[this.currentlySelected].toggleHighlight(false);
            this.currentlySelected = null;
        } else {
            if (!!commentId) {
                let isHighlighted = this.COMMENTS[commentId].toggleHighlight();
                if (isHighlighted) {
                    this.LIST.scrollTo(0, this.COMMENTS[commentId].ROOT.offsetTop - 50);
                    this.currentlySelected = commentId;
                }
            } else
                Object.values(this.COMMENTS).forEach(comment => comment.toggleHighlight(false));
        }
    }

    onCommentsReceived(comments) {
        // reset the data
        this.COMMENTS = {};
        this.LIST.innerHTML = '';

        Object.values(comments)
            // sort comments by date
            .sort((a, b) => {
                if (a.timestamp < b.timestamp) return -1;
                if (a.timestamp > b.timestamp) return 1;
                return 0;
            })
            // fill the comment panel
            .forEach((comment) => {
                let commentSidebarComment = new CommentSidebarComment(comment);
                this.COMMENTS[comment.id] = commentSidebarComment;
                this.LIST.appendChild(commentSidebarComment.ROOT);
            });
    }

    setCounter(selected) {
        let total = Object.keys(this.COMMENTS).length;
        if (selected === undefined) selected = total;
        this.COUNTER.innerText = `${selected} / ${total}`;
    }

    onFiltersChanged(comments) {
        let counter = 0;
        Object.values(comments).forEach(comment => {
            let visible =
                (!data.activeFilters.search || (data.activeFilters.search && comment.activeFilters.search)) &&
                (!data.activeFilters.lasso || (data.activeFilters.lasso && comment.activeFilters.lasso)) &&
                (!data.activeFilters.timeRange || (data.activeFilters.timeRange && comment.activeFilters.timeRange));
            this.COMMENTS[comment.id].applyFilter(visible);
            if (visible) counter++;
        });
        this.setCounter(counter);
    }

    searchSubmit() {
        let text = this.SEARCH_BOX.value;
        if (text.length >= 2)
            emitter.emit(E.COMMENT_SEARCH, text)
    }

    toggleShow() {
        this.isVisible = !this.isVisible;
        this.SIDEBAR_TOGGLE_BUTTON.children[0].classList.toggle('left', !this.isVisible);
        this.SIDEBAR_TOGGLE_BUTTON.children[0].classList.toggle('right', this.isVisible);
        if (this.isVisible) {
            this.ROOT.style.display = 'flex';
            setTimeout(() => {
                this.ROOT.style.marginRight = '0';
            }, 10)
        } else {
            this.ROOT.style.marginRight = `-500px`;
            setTimeout(() => {
                this.ROOT.style.display = 'none';
            }, 300)
        }
    }
}

class MainPanel {
    constructor() {
        this.ROOT = document.getElementById('comment-graph');
        this.DRAWING = new ComExDrawing(this.ROOT);
        this.CONFIG_PANEL = new ConfigPanel(this.ROOT);
    }
}

class TimeSelectorPanel {
    constructor() {
        this.ROOT = document.getElementById('time-selector');
        this.SLIDER = new TimeSlider(this.ROOT);
    }
}

class Elements {
    constructor() {
        this.ADD_SOURCE_MODAL = new AddSourceModalElements();
        this.SIDEBAR = new SidebarElements(this.ADD_SOURCE_MODAL.show);
        this.MAIN_PANEL = new MainPanel();
        this.TIME_SELECTOR = new TimeSelectorPanel();
        this.COMMENTS_SIDEBAR = new CommentSidebar();
    }
}

const ELEMENTS = new Elements();

export { ELEMENTS, SidebarSourceElement, getNodes };