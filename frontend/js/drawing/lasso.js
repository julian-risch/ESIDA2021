// heavily inspired by https://github.com/skokenes/d3-lasso/blob/master/src/lasso.js

import { data } from "../env/data.js";
import { E, emitter } from "../env/events.js";
import { DRAWING_CONFIG } from "./config.js";

class Lasso {
    constructor(parent, splits) {
        this.PARENT = parent;
        this.SPLITS = splits;

        // create helper elements
        this.ROOT = parent.append('g')
            .attr('class', 'lasso');
        this.OUTLINE = this.ROOT.append('path')
            .attr('class', 'drawn');
        this.CLOSE_CHORD = this.ROOT.append('path')
            .attr('class', 'chord-close');
        this.START_POINT = this.ROOT.append('circle')
            .attr('class', 'origin');


        this.clearLassoBlocked = false;
        const that = this;
        this.THUMBS_UP = this.ROOT.append('use')
            .attr('height', 50)
            .attr('width', 50)
            .attr('x', 300).attr('y', 300)
            .attr('xlink:href', 'img/thumb.svg#thumb')
            .style('fill', DRAWING_CONFIG.STYLES.DEFAULT.NODE_FILL_POS)
            .style('display', 'none')
            .on('click', this.__getOnClearHandler(1))
            .on('mouseover', () => that.clearLassoBlocked = true)
            .on('mouseout', () => that.clearLassoBlocked = false);
        this.THUMBS_DOWN = this.ROOT.append('use')
            .attr('height', 50)
            .attr('width', 50)
            .attr('x', 300).attr('y', 300)
            .attr('transform-origin', '300 300')
            .attr('transform', 'scale(-1,-1) translate(0, -66)')
            .attr('xlink:href', 'img/thumb.svg#thumb')
            .style('fill', DRAWING_CONFIG.STYLES.DEFAULT.NODE_FILL_NEG)
            .style('display', 'none')
            .on('click', this.__getOnClearHandler(-1))
            .on('mouseover', () => that.clearLassoBlocked = true)
            .on('mouseout', () => that.clearLassoBlocked = false);

        this.dragHook = d3.drag()
            .on('start', this.__dragStart.bind(this))
            .on('drag', this.__dragMove.bind(this))
            .on('end', this.__dragEnd.bind(this));

        this.selectedSplits = [];

        this.PARENT.select(function () {
            return this.parentNode;
        }).call(this.dragHook);
    }

    attachLasso() {
        this.dragHook.filter(() => true);
    }

    detachLasso() {
        this.dragHook.filter(null);
    }

    __dragStart() {
        this.drawnCoords = [];
        this.ROOT.style('display', null);
        this.OUTLINE.attr('d', null);
        this.CLOSE_CHORD.attr('d', null);
        this.outline = '';
        this.origin = '';
        this.SPLITS.nodes().forEach((comment) => {
            const box = comment.getBoundingClientRect();
            comment.__lasso = {
                possible: false,
                selected: false,
                hoverSelect: false,
                loopSelect: false,
                lassoPoint: [
                    Math.round(box.left + box.width / 2),
                    Math.round(box.top + box.height / 2)]
            };
        });
    }

    __dragMove() {
        // Get mouse position within body, used for calculations
        let x, y;
        if (d3.event.sourceEvent.type === "touchmove") {
            x = d3.event.sourceEvent.touches[0].clientX;
            y = d3.event.sourceEvent.touches[0].clientY;
        } else {
            x = d3.event.sourceEvent.clientX;
            y = d3.event.sourceEvent.clientY;
        }
        // Get mouse position within drawing area, used for rendering
        let tx = d3.mouse(this.PARENT.node())[0];
        let ty = d3.mouse(this.PARENT.node())[1];

        // Initialize the path or add the latest point to it
        if (this.outline === '') {
            this.outline += `M ${tx} ${ty}`;
            this.origin = [x, y];
            this.torigin = [tx, ty];
            // Draw origin node
            this.START_POINT
                .attr("cx", tx)
                .attr("cy", ty)
                .attr("r", 7)
                .attr("display", null);
        } else {
            this.outline += ` L ${tx} ${ty}`;
        }

        this.drawnCoords.push([x, y]);

        // Set the closed path line
        let close_draw_path = `M ${tx} ${ty} L ${this.torigin[0]} ${this.torigin[1]}`;

        // Draw the lines
        this.OUTLINE.attr('d', this.outline);
        this.CLOSE_CHORD.attr('d', close_draw_path);
    }

    __dragEnd() {
        // Remove mouseover tagging function
        this.SPLITS.on("mouseover.lasso", null);

        try {
            const that = this;
            this.SPLITS.each(function (split) {
                const box = d3.select(this).node().getBoundingClientRect();
                if (d3.polygonContains(that.drawnCoords, [
                    Math.round(box.left + box.width / 2),
                    Math.round(box.top + box.height / 2)])) {
                    data.comments[split.orig_id[0]].activeFilters.lasso = true;
                    that.selectedSplits.push(split);
                }
            });
            data.activateFilter('lasso');
            this.displayThumbs(this.torigin[0], this.torigin[1]);
        } catch (e) {
            this.__getOnClearHandler()();
        }
    }

    hideThumbs() {
        this.THUMBS_UP.style('display', 'none');
        this.THUMBS_DOWN.style('display', 'none');
    }

    displayThumbs(x, y) {
        this.THUMBS_UP
            .style('display', null)
            .attr('x', x).attr('y', y);

        this.THUMBS_DOWN
            .style('display', null)
            .attr('x', x).attr('y', y)
            .attr('transform-origin', `${x} ${y}`);
    }

    __getOnClearHandler(vote) {
        const that = this;
        return function () {
            if (vote !== undefined) {
                const commentIds = Array.from(new Set(that.selectedSplits.map(s => s.orig_id[0])));
                commentIds.forEach(commentId => data.comments[commentId].comexVotes += vote);
                that.selectedSplits.forEach(split => split.comexVotes += vote);
                console.log(`Voting ${vote > 0 ? 'up' : 'down'} on ${commentIds.length} comments from ${that.selectedSplits.length} splits.`)
                emitter.emit(E.VOTE_SUBMITTED);
            } else {
                // dragend event ALWAYS fires before click
                // the thumbs set this to true when hovered,
                // so default dragend behaviour should be blocked here.
                if (that.clearLassoBlocked) return;
            }
            that.selectedSplits = [];

            that.hideThumbs();
            that.ROOT.style('display', 'none');
            data.clearFilters('lasso');
        }
    }
}

export { Lasso };