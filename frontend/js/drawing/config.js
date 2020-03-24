import { E, emitter } from "../env/events.js";
import { getNodes } from "../env/elements.js";

const DRAWING_CONFIG = {
    HEIGHT: 80,
    WIDTH: 100,
    EDGE_TYPE_WEIGHTS: {
        REPLY_TO: 1.,
        SAME_ARTICLE: 1.,
        //SIMILARITY: 1.,
        //SAME_GROUP: 1.,
        SAME_COMMENT: 1.
    },
    CHARGE_STRENGTH: -5,
    CHARGE_MAX_DISTANCE: 50
};

class ConfigPanel {
    constructor(parent) {
        this.ROOT = document.createElement('ul');
        this.ROOT.setAttribute('id', 'config-panel');

        Object.keys(DRAWING_CONFIG.EDGE_TYPE_WEIGHTS).forEach(key =>
            this._makeSlider(`${key.toLowerCase()} weight`, 0, 1, 0.1, DRAWING_CONFIG.EDGE_TYPE_WEIGHTS, key)
        );
        this._makeSlider('charge strength', -100, 10, 1, DRAWING_CONFIG, 'CHARGE_STRENGTH');
        this._makeSlider('charge distance', 1, 200, 1, DRAWING_CONFIG, 'CHARGE_MAX_DISTANCE');

        parent.appendChild(this.ROOT);
        emitter.on(E.DRAWING_CONFIG_CHANGED, this.onChange);
    }

    onChange() {
        console.log(DRAWING_CONFIG)
    }

    _makeSlider(name, min, max, step, basevar, key) {
        let elem = getNodes(`<li><div>${name}: <span></span></div><input type="range" value="${basevar[key]}" min="${min}" max="${max}" step="${step}" /></li>`)[0];
        let input = elem.querySelector('input');
        let valElem = elem.querySelector('span');
        input.addEventListener('change', () => {
            basevar[key] = parseFloat(input.value);
            valElem.innerText = input.value;
            emitter.emit(E.DRAWING_CONFIG_CHANGED);
        });
        this.ROOT.appendChild(elem);
    }
}

export { DRAWING_CONFIG, ConfigPanel };