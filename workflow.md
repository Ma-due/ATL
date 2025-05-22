---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	receive(receive)
	fetch(fetch)
	generate(generate)
	execute(execute)
	analyze(analyze)
	__end__([<p>__end__</p>]):::last
	__start__ --> receive;
	execute --> analyze;
	generate -. &nbsp;end&nbsp; .-> __end__;
	generate -.-> analyze;
	generate -.-> execute;
	receive -. &nbsp;end&nbsp; .-> __end__;
	receive -.-> execute;
	receive -.-> fetch;
	receive -.-> generate;
	analyze --> __end__;
	fetch --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
