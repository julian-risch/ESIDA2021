import { emitter, E } from '../env/events.js'
import { data } from '../env/data.js';
import { ELEMENTS } from '../env/elements.js';
import { Layout } from './layout.js';
import { Lasso } from "./lasso.js";
import { DRAWING_CONFIG as CONFIG } from "./config.js";
import { RangeSlider } from "../libs/range-slider.js";

class TimeSlider {
    constructor(parent) {
        this.ROOT = parent;
        this.RANGE_SLIDER = undefined;

        emitter.on(E.DATA_UPDATED_COMMENTS, this.onDataUpdate.bind(this));
    }

    initRangeSlider() {
        let width = this.ROOT.clientWidth * 0.8;
        if (width < 500) width = this.ROOT.clientWidth - 20;

        // FIXME remove time constraint again!
        const maxDate = new Date('2020-01-14T00:00:00.000000');
        const comments = Object.values(data.comments)
            .filter(comment => comment.datetime < maxDate);

        this.RANGE_SLIDER = new RangeSlider()
            .container(this.ROOT)
            .data(comments)
            .accessor(comment => comment.datetime)
            .onBrush(this.onBrush)
            .svgWidth(width)
            .svgHeight(this.ROOT.clientHeight)
            .render();
    }

    onDataUpdate() {
        //if (this.RANGE_SLIDER === undefined)
        this.initRangeSlider()
        //else
        //    this.RANGE_SLIDER.updateData(Object.values(data.comments));
    }

    onBrush(d) {
        if (d.reset)
            data.clearFilters('timeRange');
        else
            data.applyFilter('timeRange', d.data.map(c => c.id));
    }
}

export { TimeSlider };