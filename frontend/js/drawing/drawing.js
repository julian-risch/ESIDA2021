import { emitter, E } from '../env/events.js'
import { data } from '../env/data.js';
import { ELEMENTS } from '../env/elements.js';
import { Layout } from './layout.js';

import { DRAWING_CONFIG as CONFIG } from "./config.js";

class Comments {
    constructor() {
        this.splits = [];
        this.lookup = {};

        let counter = 0;
        Object.keys(data.comments).forEach((commentId) => {
            this.lookup[commentId] = [];
            data.comments[commentId].splits.forEach((split, j) => {
                this.splits.push({
                    orig_id: [commentId, j],
                    text: data.getCommentText(commentId, j)
                });
                this.lookup[commentId].push(counter);
                counter++;
            });
        });
        this.edges = data.edges.map(edge => {
            try {
                return {
                    source: this.lookup[data.idx2id[edge.src[0]]][edge.src[1]],
                    target: this.lookup[data.idx2id[edge.tgt[0]]][edge.tgt[1]],
                    weights: edge.wgts,
                    src: edge.src,
                    tgt: edge.tgt
                }
            } catch (e) {
                console.log(edge);
                console.log(this.lookup);
                console.log(edge.src[0], data.idx2id[edge.src[0]], this.lookup[data.idx2id[edge.src[0]]]);
                throw e;
            }
        });

        this.highlightActive = false;

        this.eventlisteners = [
            emitter.on(E.DRAWING_CONFIG_CHANGED, this.onConfigChange.bind(this)),
            emitter.on(E.COMMENT_SELECTED, this.highlightComment.bind(this))];
    }

    draw(parent) {
        this.ROOT = parent.append('g');
        this.NODES = this.ROOT
            .selectAll('g')
            .data(this.splits)
            .join('g');

        this.NODES
            .append('circle')
            .attr('stroke', '#fff')
            .attr('stroke-width', 1.5)
            .attr('r', 5)
            .attr('fill', CONFIG.COLOURS.NODE_FILL_DEFAULT)
            .on('click', this.nodeOnClick.bind(this));

        /*this.nodes
            .append('title')
            .text(d => d.name);

        this.nodes.append('text')
            .attr('dy', -3)
            .text(d => d.name);*/

        this.LINKS = parent.append('g')
            .attr('stroke', CONFIG.COLOURS.EDGE_STROKE_DEFAULT)
            .attr('stroke-opacity', 0.6)
            .selectAll('line')
            .data(this.edges)
            .join('line')
            .attr('stroke-width', d => Math.sqrt(d.value / 50));
    }

    highlightComment(commentId) {
        commentId += '';
        let nodeOpacity = 1.0;
        this.highlightActive = !this.highlightActive;
        if (this.highlightActive)
            nodeOpacity = (d) => (d.orig_id[0] !== commentId) ? CONFIG.COLOURS.NODE_OPACITY_UNSELECTED : 1.0;

        this.NODES.attr('fill-opacity', nodeOpacity);
    }

    nodeOnClick(e) {
        this.eventlisteners.push(emitter.emit(E.COMMENT_SELECTED, e.orig_id[0]));
    }

    onTick() {
        this.LINKS
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        this.NODES
            .attr('transform', d => 'translate(' + d.x + ',' + d.y + ')');
    }

    onConfigChange(key, value) {
        if (key === 'LINKS_VISIBLE')
            this.LINKS.attr('stroke-opacity', value ? 1 : 0);
    }

    attachSimulation(simulation) {
        simulation.on('tick', this.onTick.bind(this));
        this.NODES.call(Layout.drag(simulation));
    }

    destructor() {
        this.eventlisteners.forEach((listener) => emitter.off(listener));
        this.NODES.remove();
        this.LINKS.remove();
        delete this.splits;
        delete this.lookup;
        delete this.edges;
    }
}

class ComExDrawing {
    constructor(parent) {
        this.ROOT = d3.select(parent).append('svg');
        this.MAIN_GROUP = this.ROOT.append('g');

        this.setDimensions();
        this.createScales();

        emitter.on(E.REDRAW, this.draw.bind(this));
    }

    draw() {
        this.deconstruct();

        this.initZoom();

        this.COMMENTS = new Comments();
        console.log(this.COMMENTS);

        this.COMMENTS.draw(this.MAIN_GROUP);
        this.LAYOUT = new Layout(this.COMMENTS.splits, this.COMMENTS.edges);
        this.COMMENTS.attachSimulation(this.LAYOUT.simulation);
        this.ROOT.node();
    }

    createScales() {
        this.xScale = d3.scaleLinear()
            .range([0, this.canvasWidth])
            .domain([0, CONFIG.WIDTH]);
        this.yScale = d3.scaleLinear()
            .range([0, this.canvasHeight])
            .domain([0, CONFIG.HEIGHT]);
    }

    initZoom() {
        let setExtent = zoom => zoom.extent([[0, 0], [CONFIG.WIDTH, CONFIG.HEIGHT]]);

        if (!this.ZOOM) {
            this.ZOOM = d3.zoom()
                .scaleExtent([0.1, 8])
                .on('zoom', () => {
                    this.MAIN_GROUP.attr('transform', d3.event.transform);
                });
            this.ROOT.call(this.ZOOM);
        }
        setExtent(this.ZOOM);
    }

    setDimensions() {
        let parent = this.ROOT.node().parentElement;
        this.canvasWidth = parent.clientWidth;
        this.canvasHeight = parent.clientHeight;
        CONFIG.HEIGHT = this.canvasHeight;
        CONFIG.WIDTH = this.canvasWidth;

        this.ROOT.attr('viewBox', [0, 0, this.canvasWidth, this.canvasHeight])
            .attr('height', this.canvasHeight);
    }

    deconstruct() {
        if (this.COMMENTS) {
            this.COMMENTS.destructor();
            delete this.COMMENTS;
        }
        if (this.LAYOUT) {
            this.LAYOUT.deconstructor();
            delete this.LAYOUT;
        }
    }
}

export { ComExDrawing };