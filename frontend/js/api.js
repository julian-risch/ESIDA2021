import * as d3 from './libs/d3.min'


const GET = (url) => {
    return new Promise(function (resolve, reject) {
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (this.readyState === 4) {
                if (this.status === 200) {
                    let r = this.responseXML;
                    resolve(r);
                } else {
                    reject('FAIL');
                }
            }
        };
        xhttp.open("GET", url, true);
        xhttp.send();
    });
};


class API {
    constructor() {

    }
}

export { API }