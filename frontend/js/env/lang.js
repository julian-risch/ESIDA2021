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

const LANG = {
    SOURCE: new T('Quelle', 'Source'),
    DATETIME: new T(
        (d) => `${d.getDate()}.${d.getMonth()}.${d.getFullYear()} ${d.getHours()}:${d.getMinutes()} Uhr`,
        (d) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()} ${d.getHours()}:${d.getMinutes()}`),
    COMMENTS: new T('Kommentare', 'Comments')
};

export { LANG };