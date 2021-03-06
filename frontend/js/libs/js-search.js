//https://rawgit.com/kristopolous/Porter-Stemmer/master/PorterStemmer1980.min.js
// Reference Javascript Porter Stemmer. This code corresponds to the original
// 1980 paper available here: http://tartarus.org/martin/PorterStemmer/def.txt
// The latest version of this code is available at https://github.com/kristopolous/Porter-Stemmer
//
// Original comment:
// Porter stemmer in Javascript. Few comments, but it's easy to follow against the rules in the original
// paper, in
//
//  Porter, 1980, An algorithm for suffix stripping, Program, Vol. 14,
//  no. 3, pp 130-137,
//
// see also http://www.tartarus.org/~martin/PorterStemmer

var stemmer = (function () {
    var step2list = {
            "ational": "ate",
            "tional": "tion",
            "enci": "ence",
            "anci": "ance",
            "izer": "ize",
            "bli": "ble",
            "alli": "al",
            "entli": "ent",
            "eli": "e",
            "ousli": "ous",
            "ization": "ize",
            "ation": "ate",
            "ator": "ate",
            "alism": "al",
            "iveness": "ive",
            "fulness": "ful",
            "ousness": "ous",
            "aliti": "al",
            "iviti": "ive",
            "biliti": "ble",
            "logi": "log"
        },

        step3list = {
            "icate": "ic",
            "ative": "",
            "alize": "al",
            "iciti": "ic",
            "ical": "ic",
            "ful": "",
            "ness": ""
        },

        c = "[^aeiou]",          // consonant
        v = "[aeiouy]",          // vowel
        C = c + "[^aeiouy]*",    // consonant sequence
        V = v + "[aeiou]*",      // vowel sequence

        mgr0 = "^(" + C + ")?" + V + C,               // [C]VC... is m>0
        meq1 = "^(" + C + ")?" + V + C + "(" + V + ")?$",  // [C]VC[V] is m=1
        mgr1 = "^(" + C + ")?" + V + C + V + C,       // [C]VCVC... is m>1
        s_v = "^(" + C + ")?" + v;                   // vowel in stem

    function dummyDebug() {
    }

    function realDebug() {
        //console.log(Array.prototype.slice.call(arguments).join(' '));
    }

    return function (w, debug) {
        var
            stem,
            suffix,
            firstch,
            re,
            re2,
            re3,
            re4,
            debugFunction,
            origword = w;

        if (debug) {
            debugFunction = realDebug;
        } else {
            debugFunction = dummyDebug;
        }

        if (w.length < 3) {
            return w;
        }

        firstch = w.substr(0, 1);
        if (firstch == "y") {
            w = firstch.toUpperCase() + w.substr(1);
        }

        // Step 1a
        re = /^(.+?)(ss|i)es$/;
        re2 = /^(.+?)([^s])s$/;

        if (re.test(w)) {
            w = w.replace(re, "$1$2");
            debugFunction('1a', re, w);

        } else if (re2.test(w)) {
            w = w.replace(re2, "$1$2");
            debugFunction('1a', re2, w);
        }

        // Step 1b
        re = /^(.+?)eed$/;
        re2 = /^(.+?)(ed|ing)$/;
        if (re.test(w)) {
            var fp = re.exec(w);
            re = new RegExp(mgr0);
            if (re.test(fp[1])) {
                re = /.$/;
                w = w.replace(re, "");
                debugFunction('1b', re, w);
            }
        } else if (re2.test(w)) {
            var fp = re2.exec(w);
            stem = fp[1];
            re2 = new RegExp(s_v);
            if (re2.test(stem)) {
                w = stem;
                debugFunction('1b', re2, w);

                re2 = /(at|bl|iz)$/;
                re3 = new RegExp("([^aeiouylsz])\\1$");
                re4 = new RegExp("^" + C + v + "[^aeiouwxy]$");

                if (re2.test(w)) {
                    w = w + "e";
                    debugFunction('1b', re2, w);

                } else if (re3.test(w)) {
                    re = /.$/;
                    w = w.replace(re, "");
                    debugFunction('1b', re3, w);

                } else if (re4.test(w)) {
                    w = w + "e";
                    debugFunction('1b', re4, w);
                }
            }
        }

        // Step 1c
        re = new RegExp("^(.*" + v + ".*)y$");
        if (re.test(w)) {
            var fp = re.exec(w);
            stem = fp[1];
            w = stem + "i";
            debugFunction('1c', re, w);
        }

        // Step 2
        re = /^(.+?)(ational|tional|enci|anci|izer|bli|alli|entli|eli|ousli|ization|ation|ator|alism|iveness|fulness|ousness|aliti|iviti|biliti|logi)$/;
        if (re.test(w)) {
            var fp = re.exec(w);
            stem = fp[1];
            suffix = fp[2];
            re = new RegExp(mgr0);
            if (re.test(stem)) {
                w = stem + step2list[suffix];
                debugFunction('2', re, w);
            }
        }

        // Step 3
        re = /^(.+?)(icate|ative|alize|iciti|ical|ful|ness)$/;
        if (re.test(w)) {
            var fp = re.exec(w);
            stem = fp[1];
            suffix = fp[2];
            re = new RegExp(mgr0);
            if (re.test(stem)) {
                w = stem + step3list[suffix];
                debugFunction('3', re, w);
            }
        }

        // Step 4
        re = /^(.+?)(al|ance|ence|er|ic|able|ible|ant|ement|ment|ent|ou|ism|ate|iti|ous|ive|ize)$/;
        re2 = /^(.+?)(s|t)(ion)$/;
        if (re.test(w)) {
            var fp = re.exec(w);
            stem = fp[1];
            re = new RegExp(mgr1);
            if (re.test(stem)) {
                w = stem;
                debugFunction('4', re, w);
            }
        } else if (re2.test(w)) {
            var fp = re2.exec(w);
            stem = fp[1] + fp[2];
            re2 = new RegExp(mgr1);
            if (re2.test(stem)) {
                w = stem;
                debugFunction('4', re2, w);
            }
        }

        // Step 5
        re = /^(.+?)e$/;
        if (re.test(w)) {
            var fp = re.exec(w);
            stem = fp[1];
            re = new RegExp(mgr1);
            re2 = new RegExp(meq1);
            re3 = new RegExp("^" + C + v + "[^aeiouwxy]$");
            if (re.test(stem) || (re2.test(stem) && !(re3.test(stem)))) {
                w = stem;
                debugFunction('5', re, re2, re3, w);
            }
        }

        re = /ll$/;
        re2 = new RegExp(mgr1);
        if (re.test(w) && re2.test(w)) {
            re = /.$/;
            w = w.replace(re, "");
            debugFunction('5', re, re2, w);
        }

        // and turn initial Y back to y
        if (firstch == "y") {
            w = firstch.toLowerCase() + w.substr(1);
        }


        return w;
    }
})();


'use strict';

/**
 * Indexes for all substring searches (e.g. the term "cat" is indexed as "c", "ca", "cat", "a", "at", and "t").
 */
var AllSubstringsIndexStrategy = /*#__PURE__*/function () {
    function AllSubstringsIndexStrategy() {
    }

    var _proto = AllSubstringsIndexStrategy.prototype;

    /**
     * @inheritDocs
     */
    _proto.expandToken = function expandToken(token) {
        var expandedTokens = [];
        var string;

        for (var i = 0, length = token.length; i < length; ++i) {
            string = '';

            for (var j = i; j < length; ++j) {
                string += token.charAt(j);
                expandedTokens.push(string);
            }
        }

        return expandedTokens;
    };

    return AllSubstringsIndexStrategy;
}();

/**
 * Indexes for exact word matches.
 */
var ExactWordIndexStrategy = /*#__PURE__*/function () {
    function ExactWordIndexStrategy() {
    }

    var _proto = ExactWordIndexStrategy.prototype;

    /**
     * @inheritDocs
     */
    _proto.expandToken = function expandToken(token) {
        return token ? [token] : [];
    };

    return ExactWordIndexStrategy;
}();

/**
 * Indexes for prefix searches (e.g. the term "cat" is indexed as "c", "ca", and "cat" allowing prefix search lookups).
 */
var PrefixIndexStrategy = /*#__PURE__*/function () {
    function PrefixIndexStrategy() {
    }

    var _proto = PrefixIndexStrategy.prototype;

    /**
     * @inheritDocs
     */
    _proto.expandToken = function expandToken(token) {
        var expandedTokens = [];
        var string = '';

        for (var i = 0, length = token.length; i < length; ++i) {
            string += token.charAt(i);
            expandedTokens.push(string);
        }

        return expandedTokens;
    };

    return PrefixIndexStrategy;
}();

/**
 * Enforces case-sensitive text matches.
 */
var CaseSensitiveSanitizer = /*#__PURE__*/function () {
    function CaseSensitiveSanitizer() {
    }

    var _proto = CaseSensitiveSanitizer.prototype;

    /**
     * @inheritDocs
     */
    _proto.sanitize = function sanitize(text) {
        return text ? text.trim() : '';
    };

    return CaseSensitiveSanitizer;
}();

/**
 * Sanitizes text by converting to a locale-friendly lower-case version and triming leading and trailing whitespace.
 */
var LowerCaseSanitizer = /*#__PURE__*/function () {
    function LowerCaseSanitizer() {
    }

    var _proto = LowerCaseSanitizer.prototype;

    /**
     * @inheritDocs
     */
    _proto.sanitize = function sanitize(text) {
        return text ? text.toLocaleLowerCase().trim() : '';
    };

    return LowerCaseSanitizer;
}();

/**
 * Find and return a nested object value.
 *
 * @param object to crawl
 * @param path Property path
 * @returns {any}
 */
function getNestedFieldValue(object, path) {
    path = path || [];
    object = object || {};
    var value = object; // walk down the property path

    for (var i = 0; i < path.length; i++) {
        value = value[path[i]];

        if (value == null) {
            return null;
        }
    }

    return value;
}

/**
 * Search index capable of returning results matching a set of tokens and ranked according to TF-IDF.
 */
var TfIdfSearchIndex = /*#__PURE__*/function () {
    function TfIdfSearchIndex(uidFieldName) {
        this._uidFieldName = uidFieldName;
        this._tokenToIdfCache = {};
        this._tokenMap = {};
    }

    /**
     * @inheritDocs
     */


    var _proto = TfIdfSearchIndex.prototype;

    _proto.indexDocument = function indexDocument(token, uid, doc) {
        this._tokenToIdfCache = {}; // New index invalidates previous IDF caches

        var tokenMap = this._tokenMap;
        var tokenDatum;

        if (typeof tokenMap[token] !== 'object') {
            tokenMap[token] = tokenDatum = {
                $numDocumentOccurrences: 0,
                $totalNumOccurrences: 1,
                $uidMap: {}
            };
        } else {
            tokenDatum = tokenMap[token];
            tokenDatum.$totalNumOccurrences++;
        }

        var uidMap = tokenDatum.$uidMap;

        if (typeof uidMap[uid] !== 'object') {
            tokenDatum.$numDocumentOccurrences++;
            uidMap[uid] = {
                $document: doc,
                $numTokenOccurrences: 1
            };
        } else {
            uidMap[uid].$numTokenOccurrences++;
        }
    }
    /**
     * @inheritDocs
     */
    ;

    _proto.search = function search(tokens, corpus) {
        var uidToDocumentMap = {};

        for (var i = 0, numTokens = tokens.length; i < numTokens; i++) {
            var token = tokens[i];
            var tokenMetadata = this._tokenMap[token]; // Short circuit if no matches were found for any given token.

            if (!tokenMetadata) {
                return [];
            }

            if (i === 0) {
                var keys = Object.keys(tokenMetadata.$uidMap);

                for (var j = 0, numKeys = keys.length; j < numKeys; j++) {
                    var uid = keys[j];
                    uidToDocumentMap[uid] = tokenMetadata.$uidMap[uid].$document;
                }
            } else {
                var keys = Object.keys(uidToDocumentMap);

                for (var j = 0, numKeys = keys.length; j < numKeys; j++) {
                    var uid = keys[j];

                    if (typeof tokenMetadata.$uidMap[uid] !== 'object') {
                        delete uidToDocumentMap[uid];
                    }
                }
            }
        }

        var documents = [];

        for (var uid in uidToDocumentMap) {
            documents.push(uidToDocumentMap[uid]);
        }

        var calculateTfIdf = this._createCalculateTfIdf(); // Return documents sorted by TF-IDF


        return documents.sort(function (documentA, documentB) {
            return calculateTfIdf(tokens, documentB, corpus) - calculateTfIdf(tokens, documentA, corpus);
        });
    };

    _proto._createCalculateIdf = function _createCalculateIdf() {
        var tokenMap = this._tokenMap;
        var tokenToIdfCache = this._tokenToIdfCache;
        return function calculateIdf(token, documents) {
            if (!tokenToIdfCache[token]) {
                var numDocumentsWithToken = typeof tokenMap[token] !== 'undefined' ? tokenMap[token].$numDocumentOccurrences : 0;
                tokenToIdfCache[token] = 1 + Math.log(documents.length / (1 + numDocumentsWithToken));
            }

            return tokenToIdfCache[token];
        };
    };

    _proto._createCalculateTfIdf = function _createCalculateTfIdf() {
        var tokenMap = this._tokenMap;
        var uidFieldName = this._uidFieldName;

        var calculateIdf = this._createCalculateIdf();

        return function calculateTfIdf(tokens, document, documents) {
            var score = 0;

            for (var i = 0, numTokens = tokens.length; i < numTokens; ++i) {
                var token = tokens[i];
                var inverseDocumentFrequency = calculateIdf(token, documents);

                if (inverseDocumentFrequency === Infinity) {
                    inverseDocumentFrequency = 0;
                }

                var uid;

                if (uidFieldName instanceof Array) {
                    uid = document && getNestedFieldValue(document, uidFieldName);
                } else {
                    uid = document && document[uidFieldName];
                }

                var termFrequency = typeof tokenMap[token] !== 'undefined' && typeof tokenMap[token].$uidMap[uid] !== 'undefined' ? tokenMap[token].$uidMap[uid].$numTokenOccurrences : 0;
                score += termFrequency * inverseDocumentFrequency;
            }

            return score;
        };
    };

    return TfIdfSearchIndex;
}();

/**
 * Search index capable of returning results matching a set of tokens but without any meaningful rank or order.
 */
var UnorderedSearchIndex = /*#__PURE__*/function () {
    function UnorderedSearchIndex() {
        this._tokenToUidToDocumentMap = {};
    }

    /**
     * @inheritDocs
     */


    var _proto = UnorderedSearchIndex.prototype;

    _proto.indexDocument = function indexDocument(token, uid, doc) {
        if (typeof this._tokenToUidToDocumentMap[token] !== 'object') {
            this._tokenToUidToDocumentMap[token] = {};
        }

        this._tokenToUidToDocumentMap[token][uid] = doc;
    }
    /**
     * @inheritDocs
     */
    ;

    _proto.search = function search(tokens, corpus) {
        var intersectingDocumentMap = {};
        var tokenToUidToDocumentMap = this._tokenToUidToDocumentMap;

        for (var i = 0, numTokens = tokens.length; i < numTokens; i++) {
            var token = tokens[i];
            var documentMap = tokenToUidToDocumentMap[token]; // Short circuit if no matches were found for any given token.

            if (!documentMap) {
                return [];
            }

            if (i === 0) {
                var keys = Object.keys(documentMap);

                for (var j = 0, numKeys = keys.length; j < numKeys; j++) {
                    var uid = keys[j];
                    intersectingDocumentMap[uid] = documentMap[uid];
                }
            } else {
                var keys = Object.keys(intersectingDocumentMap);

                for (var j = 0, numKeys = keys.length; j < numKeys; j++) {
                    var uid = keys[j];

                    if (typeof documentMap[uid] !== 'object') {
                        delete intersectingDocumentMap[uid];
                    }
                }
            }
        }

        var keys = Object.keys(intersectingDocumentMap);
        var documents = [];

        for (var i = 0, numKeys = keys.length; i < numKeys; i++) {
            var uid = keys[i];
            documents.push(intersectingDocumentMap[uid]);
        }

        return documents;
    };

    return UnorderedSearchIndex;
}();

var REGEX = /[^a-zа-яё0-9\-']+/i;
/**
 * Simple tokenizer that splits strings on whitespace characters and returns an array of all non-empty substrings.
 */

var SimpleTokenizer = /*#__PURE__*/function () {
    function SimpleTokenizer() {
    }

    var _proto = SimpleTokenizer.prototype;

    /**
     * @inheritDocs
     */
    _proto.tokenize = function tokenize(text) {
        return text.split(REGEX).filter(function (text) {
                return text;
            } // Filter empty tokens
        );
    };

    return SimpleTokenizer;
}();

/**
 * Stemming is the process of reducing search tokens to their root (or stem) so that searches for different forms of a
 * word will match. For example "search", "searching" and "searched" are all reduced to the stem "search".
 *
 * <p>This stemming tokenizer converts tokens (words) to their stem forms before returning them. It requires an
 * external stemming function to be provided; for this purpose I recommend the NPM 'porter-stemmer' library.
 *
 * <p>For more information see http : //tartarus.org/~martin/PorterStemmer/
 */
var StemmingTokenizer = /*#__PURE__*/function () {
    /**
     * Constructor.
     *
     * @param stemmingFunction Function capable of accepting a word and returning its stem.
     * @param decoratedIndexStrategy Index strategy to be run after all stop words have been removed.
     */
    function StemmingTokenizer(stemmingFunction, decoratedTokenizer) {
        this._stemmingFunction = stemmingFunction;
        this._tokenizer = decoratedTokenizer;
    }

    /**
     * @inheritDocs
     */


    var _proto = StemmingTokenizer.prototype;

    _proto.tokenize = function tokenize(text) {
        return this._tokenizer.tokenize(text).map(this._stemmingFunction);
    };

    return StemmingTokenizer;
}();

/**
 * Stop words list copied from Lunr JS.
 */
var StopWordsMap = {
    a: true,
    able: true,
    about: true,
    across: true,
    after: true,
    all: true,
    almost: true,
    also: true,
    am: true,
    among: true,
    an: true,
    and: true,
    any: true,
    are: true,
    as: true,
    at: true,
    be: true,
    because: true,
    been: true,
    but: true,
    by: true,
    can: true,
    cannot: true,
    could: true,
    dear: true,
    did: true,
    'do': true,
    does: true,
    either: true,
    'else': true,
    ever: true,
    every: true,
    'for': true,
    from: true,
    'get': true,
    got: true,
    had: true,
    has: true,
    have: true,
    he: true,
    her: true,
    hers: true,
    him: true,
    his: true,
    how: true,
    however: true,
    i: true,
    'if': true,
    'in': true,
    into: true,
    is: true,
    it: true,
    its: true,
    just: true,
    least: true,
    "let": true,
    like: true,
    likely: true,
    may: true,
    me: true,
    might: true,
    most: true,
    must: true,
    my: true,
    neither: true,
    no: true,
    nor: true,
    not: true,
    of: true,
    off: true,
    often: true,
    on: true,
    only: true,
    or: true,
    other: true,
    our: true,
    own: true,
    rather: true,
    said: true,
    say: true,
    says: true,
    she: true,
    should: true,
    since: true,
    so: true,
    some: true,
    than: true,
    that: true,
    the: true,
    their: true,
    them: true,
    then: true,
    there: true,
    these: true,
    they: true,
    'this': true,
    tis: true,
    to: true,
    too: true,
    twas: true,
    us: true,
    wants: true,
    was: true,
    we: true,
    were: true,
    what: true,
    when: true,
    where: true,
    which: true,
    'while': true,
    who: true,
    whom: true,
    why: true,
    will: true,
    'with': true,
    would: true,
    yet: true,
    you: true,
    your: true
}; // Prevent false positives for inherited properties

StopWordsMap.constructor = false;
StopWordsMap.hasOwnProperty = false;
StopWordsMap.isPrototypeOf = false;
StopWordsMap.propertyIsEnumerable = false;
StopWordsMap.toLocaleString = false;
StopWordsMap.toString = false;
StopWordsMap.valueOf = false;

/**
 * Stop words are very common (e.g. "a", "and", "the") and are often not semantically meaningful in the context of a
 * search. This tokenizer removes stop words from a set of tokens before passing the remaining tokens along for
 * indexing or searching purposes.
 */

var StopWordsTokenizer = /*#__PURE__*/function () {
    /**
     * Constructor.
     *
     * @param decoratedIndexStrategy Index strategy to be run after all stop words have been removed.
     */
    function StopWordsTokenizer(decoratedTokenizer) {
        this._tokenizer = decoratedTokenizer;
    }

    /**
     * @inheritDocs
     */


    var _proto = StopWordsTokenizer.prototype;

    _proto.tokenize = function tokenize(text) {
        return this._tokenizer.tokenize(text).filter(function (token) {
            return !StopWordsMap[token];
        });
    };

    return StopWordsTokenizer;
}();

function _defineProperties(target, props) {
    for (var i = 0; i < props.length; i++) {
        var descriptor = props[i];
        descriptor.enumerable = descriptor.enumerable || false;
        descriptor.configurable = true;
        if ("value" in descriptor) descriptor.writable = true;
        Object.defineProperty(target, descriptor.key, descriptor);
    }
}

function _createClass(Constructor, protoProps, staticProps) {
    if (protoProps) _defineProperties(Constructor.prototype, protoProps);
    if (staticProps) _defineProperties(Constructor, staticProps);
    return Constructor;
}

/**
 * Simple client-side searching within a set of documents.
 *
 * <p>Documents can be searched by any number of fields. Indexing and search strategies are highly customizable.
 */
var Search = /*#__PURE__*/function () {
    /**
     * Array containing either a property name or a path (list of property names) to a nested value
     */

    /**
     * Constructor.
     * @param uidFieldName Field containing values that uniquely identify search documents; this field's values are used
     *                     to ensure that a search result set does not contain duplicate objects.
     */
    function Search(uidFieldName) {
        if (!uidFieldName) {
            throw Error('js-search requires a uid field name constructor parameter');
        }

        this._uidFieldName = uidFieldName; // Set default/recommended strategies

        this._indexStrategy = new PrefixIndexStrategy();
        this._searchIndex = new TfIdfSearchIndex(uidFieldName);
        this._sanitizer = new LowerCaseSanitizer();
        this._tokenizer = new SimpleTokenizer();
        this._documents = [];
        this._searchableFields = [];
    }

    /**
     * Override the default index strategy.
     * @param value Custom index strategy
     * @throws Error if documents have already been indexed by this search instance
     */


    var _proto = Search.prototype;

    /**
     * Add a searchable document to the index. Document will automatically be indexed for search.
     * @param document
     */
    _proto.addDocument = function addDocument(document) {
        this.addDocuments([document]);
    }
    /**
     * Adds searchable documents to the index. Documents will automatically be indexed for search.
     * @param document
     */
    ;

    _proto.addDocuments = function addDocuments(documents) {
        this._documents = this._documents.concat(documents);
        this.indexDocuments_(documents, this._searchableFields);
    }
    /**
     * Add a new searchable field to the index. Existing documents will automatically be indexed using this new field.
     *
     * @param field Searchable field or field path. Pass a string to index a top-level field and an array of strings for nested fields.
     */
    ;

    _proto.addIndex = function addIndex(field) {
        this._searchableFields.push(field);

        this.indexDocuments_(this._documents, [field]);
    }
    /**
     * Search all documents for ones matching the specified query text.
     * @param query
     * @returns {Array<Object>}
     */
    ;

    _proto.search = function search(query) {
        var tokens = this._tokenizer.tokenize(this._sanitizer.sanitize(query));

        return this._searchIndex.search(tokens, this._documents);
    }
    /**
     * @param documents
     * @param _searchableFields Array containing property names and paths (lists of property names) to nested values
     * @private
     */
    ;

    _proto.indexDocuments_ = function indexDocuments_(documents, _searchableFields) {
        this._initialized = true;
        var indexStrategy = this._indexStrategy;
        var sanitizer = this._sanitizer;
        var searchIndex = this._searchIndex;
        var tokenizer = this._tokenizer;
        var uidFieldName = this._uidFieldName;

        for (var di = 0, numDocuments = documents.length; di < numDocuments; di++) {
            var doc = documents[di];
            var uid;

            if (uidFieldName instanceof Array) {
                uid = getNestedFieldValue(doc, uidFieldName);
            } else {
                uid = doc[uidFieldName];
            }

            for (var sfi = 0, numSearchableFields = _searchableFields.length; sfi < numSearchableFields; sfi++) {
                var fieldValue;
                var searchableField = _searchableFields[sfi];

                if (searchableField instanceof Array) {
                    fieldValue = getNestedFieldValue(doc, searchableField);
                } else {
                    fieldValue = doc[searchableField];
                }

                if (fieldValue != null && typeof fieldValue !== 'string' && fieldValue.toString) {
                    fieldValue = fieldValue.toString();
                }

                if (typeof fieldValue === 'string') {
                    var fieldTokens = tokenizer.tokenize(sanitizer.sanitize(fieldValue));

                    for (var fti = 0, numFieldValues = fieldTokens.length; fti < numFieldValues; fti++) {
                        var fieldToken = fieldTokens[fti];
                        var expandedTokens = indexStrategy.expandToken(fieldToken);

                        for (var eti = 0, nummExpandedTokens = expandedTokens.length; eti < nummExpandedTokens; eti++) {
                            var expandedToken = expandedTokens[eti];
                            searchIndex.indexDocument(expandedToken, uid, doc);
                        }
                    }
                }
            }
        }
    };

    _createClass(Search, [{
        key: "indexStrategy",
        set: function set(value) {
            if (this._initialized) {
                throw Error('IIndexStrategy cannot be set after initialization');
            }

            this._indexStrategy = value;
        },
        get: function get() {
            return this._indexStrategy;
        }
        /**
         * Override the default text sanitizing strategy.
         * @param value Custom text sanitizing strategy
         * @throws Error if documents have already been indexed by this search instance
         */

    }, {
        key: "sanitizer",
        set: function set(value) {
            if (this._initialized) {
                throw Error('ISanitizer cannot be set after initialization');
            }

            this._sanitizer = value;
        },
        get: function get() {
            return this._sanitizer;
        }
        /**
         * Override the default search index strategy.
         * @param value Custom search index strategy
         * @throws Error if documents have already been indexed
         */

    }, {
        key: "searchIndex",
        set: function set(value) {
            if (this._initialized) {
                throw Error('ISearchIndex cannot be set after initialization');
            }

            this._searchIndex = value;
        },
        get: function get() {
            return this._searchIndex;
        }
        /**
         * Override the default text tokenizing strategy.
         * @param value Custom text tokenizing strategy
         * @throws Error if documents have already been indexed by this search instance
         */

    }, {
        key: "tokenizer",
        set: function set(value) {
            if (this._initialized) {
                throw Error('ITokenizer cannot be set after initialization');
            }

            this._tokenizer = value;
        },
        get: function get() {
            return this._tokenizer;
        }
    }]);

    return Search;
}();

/**
 * This utility highlights the occurrences of tokens within a string of text. It can be used to give visual indicators
 * of match criteria within searchable fields.
 *
 * <p>For performance purposes this highlighter only works with full-word or prefix token indexes.
 */
var TokenHighlighter = /*#__PURE__*/function () {
    /**
     * Constructor.
     *
     * @param opt_indexStrategy Index strategy used by Search
     * @param opt_sanitizer Sanitizer used by Search
     * @param opt_wrapperTagName Optional wrapper tag name; defaults to 'mark' (e.g. <mark>)
     */
    function TokenHighlighter(opt_indexStrategy, opt_sanitizer, opt_wrapperTagName) {
        this._indexStrategy = opt_indexStrategy || new PrefixIndexStrategy();
        this._sanitizer = opt_sanitizer || new LowerCaseSanitizer();
        this._wrapperTagName = opt_wrapperTagName || 'mark';
    }

    /**
     * Highlights token occurrences within a string by wrapping them with a DOM element.
     *
     * @param text e.g. "john wayne"
     * @param tokens e.g. ["wa"]
     * @returns {string} e.g. "john <mark>wa</mark>yne"
     */


    var _proto = TokenHighlighter.prototype;

    _proto.highlight = function highlight(text, tokens) {
        var tagsLength = this._wrapText('').length;

        var tokenDictionary = Object.create(null); // Create a token map for easier lookup below.

        for (var i = 0, numTokens = tokens.length; i < numTokens; i++) {
            var token = this._sanitizer.sanitize(tokens[i]);

            var expandedTokens = this._indexStrategy.expandToken(token);

            for (var j = 0, numExpandedTokens = expandedTokens.length; j < numExpandedTokens; j++) {
                var expandedToken = expandedTokens[j];

                if (!tokenDictionary[expandedToken]) {
                    tokenDictionary[expandedToken] = [token];
                } else {
                    tokenDictionary[expandedToken].push(token);
                }
            }
        } // Track actualCurrentWord and sanitizedCurrentWord separately in case we encounter nested tags.


        var actualCurrentWord = '';
        var sanitizedCurrentWord = '';
        var currentWordStartIndex = 0; // Note this assumes either prefix or full word matching.

        for (var i = 0, textLength = text.length; i < textLength; i++) {
            var character = text.charAt(i);

            if (character === ' ') {
                actualCurrentWord = '';
                sanitizedCurrentWord = '';
                currentWordStartIndex = i + 1;
            } else {
                actualCurrentWord += character;
                sanitizedCurrentWord += this._sanitizer.sanitize(character);
            }

            if (tokenDictionary[sanitizedCurrentWord] && tokenDictionary[sanitizedCurrentWord].indexOf(sanitizedCurrentWord) >= 0) {
                actualCurrentWord = this._wrapText(actualCurrentWord);
                text = text.substring(0, currentWordStartIndex) + actualCurrentWord + text.substring(i + 1);
                i += tagsLength;
                textLength += tagsLength;
            }
        }

        return text;
    }
    /**
     * @param text to wrap
     * @returns Text wrapped by wrapper tag (e.g. "foo" becomes "<mark>foo</mark>")
     * @private
     */
    ;

    _proto._wrapText = function _wrapText(text) {
        var tagName = this._wrapperTagName;
        return "<" + tagName + ">" + text + "</" + tagName + ">";
    };

    return TokenHighlighter;
}();



export {
    AllSubstringsIndexStrategy, CaseSensitiveSanitizer, ExactWordIndexStrategy, LowerCaseSanitizer,
    PrefixIndexStrategy, Search, SimpleTokenizer, StemmingTokenizer, StopWordsMap, StopWordsTokenizer,
    TfIdfSearchIndex, TokenHighlighter, UnorderedSearchIndex, stemmer
}