// FIXME: add something to dynamically set the language
const LANGUAGE = ['de', 'en'][0];

class T {
    constructor(de, en = null) {
        this.de = de;
        this.en = (!!en) ? de : en;
    }

    get s() {
        return (LANGUAGE === 'de') ? this.de : this.en;
    }

    fmt(params) {
        const names = Object.keys(params);
        const vals = Object.values(params);
        return new Function(...names, `return \`${this}\`;`)(...vals);
    }
}

const zeroPad = (num) => ((num < 10) ? '0' : '') + num;
const FORMAT_DATE = {
    'dd.mm.YYYY HH:MM': (d) =>
        `${zeroPad(d.getDate())}.${zeroPad(d.getMonth() + 1)}.${d.getFullYear()} ${zeroPad(d.getHours())}:${zeroPad(d.getMinutes())}`,
    'YYYY-mm-dd HH:MM': (d) =>
        `${d.getFullYear()}-${zeroPad(d.getMonth() + 1)}-${zeroPad(d.getDate())} ${zeroPad(d.getHours())}:${zeroPad(d.getMinutes())}`
};

const LANG = {
    SOURCE: new T('Quelle', 'Source'),
    DATETIME: new T(
        (d) => `${FORMAT_DATE["dd.mm.YYYY HH:MM"](d)} Uhr`,
        FORMAT_DATE["YYYY-mm-dd HH:MM"]),
    COMMENTS: new T('Kommentare', 'Comments'),
    EMPTY_EXAMPLE: new T('Benutzerdefiniert', 'User defined')
};

export { LANG, FORMAT_DATE };