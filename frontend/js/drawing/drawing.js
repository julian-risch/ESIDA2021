import { emitter, E } from "../env/events.js"
import { data } from "../env/data.js";
import { ELEMENTS } from "../env/elements.js";

let chart = (height, width) => {
    const links = data.links.map(d => Object.create(d));
    const nodes = data.nodes.map(d => Object.create(d));

    const boxingForce = () => {
        let margin = 10;
        for (let node of nodes) {
            // Of the positions exceed the box, set them to the boundary position.
            // You may want to include your nodes width to not overlap with the box.
            node.x = Math.max(margin, Math.min(width - margin, node.x));
            node.y = Math.max(margin, Math.min(height - margin, node.y));
        }
    };

    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id)
            .strength(link => 1 / Math.min(data.nodes[link.source.index].count, data.nodes[link.target.index].count) + Math.sqrt(data.links[link.index].value / 574))
            .iterations(1))
        .force("charge", d3.forceManyBody().strength(-180).distanceMax(300))
        .force("collide", d3.forceCollide().radius(15))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("bounds", boxingForce);

    const svg = d3.create("svg")
        .attr("viewBox", [0, 0, width, height])
        .attr("height", height);

    const mainGroup = svg.append("g");

    svg.call(d3.zoom()
        .extent([[0, 0], [width, height]])
        .scaleExtent([1, 8])
        .on("zoom", zoomed));

    function zoomed() {
        mainGroup.attr("transform", d3.event.transform);
    }

    const link = mainGroup.append("g")
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6)
        .selectAll("line")
        .data(links)
        .join("line")
        .attr("stroke-width", d => Math.sqrt(d.value / 50));

    const node = mainGroup.append("g")
        .selectAll("g")
        .data(nodes)
        .join("g")
        .call(drag(simulation));

    node.append("circle")
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.5)
        .attr("r", 5)
        .attr("fill", '#da2d00');

    node.append("title")
        .text(d => d.name);

    node.append("text")
        .attr("dy", -3)
        .text(d => d.name);

    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node
            //.attr("cx", d => d.x)
            //.attr("cy", d => d.y);
            .attr("transform", d => "translate(" + d.x + "," + d.y + ")");
    });

    //invalidation.then(() => simulation.stop());

    return svg.node();
};
let drag = simulation => {

    function dragstarted(d) {
        if (!d3.event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }

    function dragended(d) {
        if (!d3.event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    return d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
};

class Comments {
    constructor() {
        this.splits = [];
        this.lookup = {};

        let counter = 0;
        Object.keys(data.comments).forEach((commentId) => {
            this.lookup[commentId] = [];
            data.comments[commentId].splits.forEach((split, j) => {
                this.splits.push({
                    id: [commentId, j],
                    text: data.getCommentText(commentId, j)
                });
                this.lookup[commentId].push(counter);
                counter++;
            });
        });
        this.edges = data.edges.map(edge => {
            return {
                source: this.lookup[data.idx2id[edge.src[0]]][edge.src[1]],
                target: this.lookup[data.idx2id[edge.tgt[0]]][edge.tgt[1]],
                weights: edge.wgts,
                src: edge.src,
                tgt: edge.tgt
            }
        });
    }
}

class ComExDrawing {
    constructor() {
        let initDims = ELEMENTS.MAIN_PANEL.getDimensions();
        this.width = initDims[0];
        this.height = initDims[1];
        this.ROOT = d3.select(ELEMENTS.MAIN_PANEL.ROOT).append('svg');
        this.ROOT.attr("viewBox", [0, 0, this.width, this.height])
            .attr("height", this.height);


        emitter.on(E.REDRAW, this.update.bind(this));
    }

    update() {
        this.COMMENTS = new Comments();
        console.log(this.COMMENTS)
        const node = this.ROOT.append("g")
            .selectAll("g")
            .data(data)
            .join("g")
            .call(drag(simulation));

        node.append("circle")
            .attr("stroke", "#fff")
            .attr("stroke-width", 1.5)
            .attr("r", 5)
            .attr("fill", '#da2d00');

        node.append("title")
            .text(d => d.name);

        node.append("text")
            .attr("dy", -3)
            .text(d => d.name);
    }
}

let drawing = new ComExDrawing();
export { drawing };