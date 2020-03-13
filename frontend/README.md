# ComEx Frontend


## Some D3.js Inspiration
* Clustered Force Layout III   
  https://bl.ocks.org/mbostock/7881887
* Force Layout Cells   
  https://observablehq.com/@giorgi-ghviniashvili/force-layout-cells
* Force bead clusters   
  https://observablehq.com/@es42289/force-bead-clusters-for-breaking-down-respondent-demograp
* Normal Force Layout   
  https://observablehq.com/@danielbustillos/network-of-stack-overflow-tags
* Group in a box network layout   
  https://observablehq.com/@cbuie/group-in-a-box-layout
* Wiggly noodle edges  
  https://bl.ocks.org/GerHobbelt/3104394
* Collapsible force layout  
  https://bl.ocks.org/mbostock/1062288   
  https://bl.ocks.org/mbostock/1093130
* Collabsible layout with hull   
  http://bl.ocks.org/GerHobbelt/3071239
  
## TinyEmitter
https://github.com/scottcorgan/tiny-emitter

### Usage

```js
var Emitter = require('tiny-emitter');
var emitter = new Emitter();

emitter.on('some-event', function (arg1, arg2, arg3) {
 //
});

emitter.emit('some-event', 'arg1 value', 'arg2 value', 'arg3 value');
```

Alternatively, you can skip the initialization step by requiring `tiny-emitter/instance` instead. This pulls in an already initialized emitter.

```js
var emitter = require('tiny-emitter/instance');

emitter.on('some-event', function (arg1, arg2, arg3) {
 //
});

emitter.emit('some-event', 'arg1 value', 'arg2 value', 'arg3 value');
```

### Instance Methods

#### on(event, callback[, context])

Subscribe to an event

* `event` - the name of the event to subscribe to
* `callback` - the function to call when event is emitted
* `context` - (OPTIONAL) - the context to bind the event callback to

#### once(event, callback[, context])

Subscribe to an event only **once**

* `event` - the name of the event to subscribe to
* `callback` - the function to call when event is emitted
* `context` - (OPTIONAL) - the context to bind the event callback to

#### off(event[, callback])

Unsubscribe from an event or all events. If no callback is provided, it unsubscribes you from all events.

* `event` - the name of the event to unsubscribe from
* `callback` - the function used when binding to the event

#### emit(event[, arguments...])

Trigger a named event

* `event` - the event name to emit
* `arguments...` - any number of arguments to pass to the event subscribers