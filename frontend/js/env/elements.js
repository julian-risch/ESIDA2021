import { LANG } from './lang.js';


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


class AddSourceModalElements {
    constructor() {
        this.ROOT = document.getElementById('add-source-modal');
        this.CLOSE_BUTTON = document.querySelector('#add-source-modal .close');
        this.URL = document.querySelector('#add-source-modal input');
        this.SUBMIT = document.querySelector('#add-source-modal .button');

        this._initStaticListeners()
    }

    hide(e) {
        if (!!e)
            e.stopPropagation();
        // prevent bubbling
        // if (!!e && !(e.target === this.ROOT || e.target === this.CLOSE_BUTTON))
        //  return;

        this.ROOT.style.display = 'none';
    }

    show() {
        this.ROOT.style.display = 'block';
    }

    _initStaticListeners() {
        let hide = this.hide.bind(this);
        this.ROOT.addEventListener('click', (e) => {
            if (e.target === this.ROOT) {
                e.stopPropagation();
                hide();
            }
        });
        this.CLOSE_BUTTON.addEventListener('click', hide);
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
        this.ROOT = nElem({ tag: 'div', cls: 'source' });
        if (!src && !url && !title && !date && !comments) {
            this._initEmpty(num, openModalFunc);
        } else {
            this.update(num, src, url, title, date, comments);
        }
    }

    _initEmpty(num, openModalFunc) {
        this.ROOT.innerHTML = `
            <h1>${LANG.SOURCE.s} ${num}</h1>
            <div class="add">+</div>`;
        this.ROOT.querySelector('div.add').addEventListener('click', openModalFunc);
    }

    update(num, src, url, title, date, num_comments) {
        this.ROOT.innerHTML = `
        <h1>Quelle ${num}</h1>
            <div class="platform"><img src="${SOURCES[src].icon}" alt="" /> ${SOURCES[src].name}</div>
            <h2>
                <a href="${url}">${title}</a></h2>
            <div class="info">
                <time datetime="${LANG.DATETIME.en(date)}">${LANG.DATETIME.s(date)}</time>
                <span class="comments">${num_comments} ${LANG.COMMENTS.s}</span>
            </div>`;
    }
}

class SidebarElements {
    constructor(openModalFunc) {
        this.openModalFunc = openModalFunc;
        this.ROOT = document.getElementById('sources');
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
        this.SIDEBAR = new SidebarElements(this.ADD_SOURCE_MODAL.show.bind(this.ADD_SOURCE_MODAL));

        this.SIDEBAR.addSource('zeit',
            'https://www.zeit.de/digital/internet/2020-03/fake-news-coronavirus-falschnachrichten-luegen-panikmache',
            'So erkennen Sie, welche Nachrichten zum Coronavirus stimmen',
            new Date(2020, 3, 16, 13, 32), 175);
        this.SIDEBAR.addEmptySource()
    }

    get tmp() {
        return 'ads'
    }
}

const ELEMENTS = new Elements();

export { ELEMENTS, SidebarSourceElement };