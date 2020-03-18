import { LANG, FORMAT_DATE } from './lang.js';
import { EXAMPLE_STORIES } from "./examples.js";
import { emitter } from "../libs/tinyemitter.js"
import { SCRAPERS } from "../api.js";

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
            if (SCRAPERS.isValidURL(this.url)) {
                emitter.emit('newSourceURL', this.url);
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
        emitter.once('newSourceURL', (data) => {
            button.innerHTML = LOADER;
        });
        emitter.once('receivedArticle', (d) => {
            this.update(d.payload.source, d.payload.url, d.payload.title, d.payload.dateObj, d.payload.comments.length);
        })
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
                elem.addEventListener('change', (e) => {
                    emitter.emit('selectexample', story)
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

class Elements {
    constructor() {
        this.ADD_SOURCE_MODAL = new AddSourceModalElements();
        this.SIDEBAR = new SidebarElements(this.ADD_SOURCE_MODAL.show);
    }
}

const ELEMENTS = new Elements();

export { ELEMENTS, SidebarSourceElement };