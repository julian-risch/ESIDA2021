// heavily inspired by https://github.com/skokenes/d3-lasso/blob/master/src/lasso.js

class Lasso {
    constructor(parent, comments) {
        this.PARENT = parent;
        this.COMMENTS = comments;
        this.ROOT = parent.append('g')
            .attr('class', 'lasso');

        this.OUTLINE = this.ROOT.append('path')
            .attr('class', 'drawn');
        this.CLOSE_CHORD = this.ROOT.append('path')
            .attr('class', 'chord-close');
        this.START_POINT = this.ROOT.append('circle')
            .attr('class', 'origin');

        this.dragHook = d3.drag()
            .on('start', this.dragStart.bind(this))
            .on('drag', this.dragMove.bind(this))
            .on('end', this.dragEnd.bind(this));
    }

    attachLasso() {
        this.PARENT.call(this.dragHook);
    }

    dragStart() {
        this.drawnCoords = [];
        this.OUTLINE.attr('d', null);
        this.CLOSE_CHORD.attr('d', null);
        this.outline = '';
        this.origin = '';
        this.COMMENTS.nodes().forEach((comment) => {
            let box = comment.getBoundingClientRect();
            comment.__lasso = {
                possible: false,
                selected: false,
                hoverSelect: false,
                loopSelect: false,
                lassoPoint: [Math.round(box.left + box.width / 2), Math.round(box.top + box.height / 2)]
            };
        });

        /*
        // if hover is on, add hover function
        if(hoverSelect) {
            items.on("mouseover.lasso",function() {
                // if hovered, change lasso selection attribute to true
                this.__lasso.hoverSelect = true;
            });
        }

        // Run user defined start function
        on.start();
         */
    }

    dragMove() {
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

        // Calculate the current distance from the lasso origin
        let distance = Math.sqrt(Math.pow(x - this.origin[0], 2) + Math.pow(y - this.origin[1], 2));

        // Set the closed path line
        let close_draw_path = `M ${tx} ${ty} L ${this.torigin[0]} ${this.torigin[1]}`;

        // Draw the lines
        this.OUTLINE.attr('d', this.outline);

        this.CLOSE_CHORD.attr('d', close_draw_path);

        // Check if the path is closed
        let isPathClosed = true;// TODO: check what the closePathDist is for
        // let isPathClosed = distance <= closePathDistance ? true : false;
        let closePathSelect = true; // TODO check what this is
        
        // If within the closed path distance parameter, show the closed path. otherwise, hide it
        if (isPathClosed && closePathSelect) {
            this.CLOSE_CHORD.attr('display', null);
        } else {
            this.CLOSE_CHORD.attr('display', 'none');
        }
/*
        items.nodes().forEach(function (n) {
            n.__lasso.loopSelect = (isPathClosed && closePathSelect) ? (classifyPoint(drawnCoords, n.__lasso.lassoPoint) < 1) : false;
            n.__lasso.possible = n.__lasso.hoverSelect || n.__lasso.loopSelect;
        });
*/
        //on.draw();
    }

    dragEnd() {

        console.log('dragend')
    }


}

export { Lasso };