# Class diagrams with a moving focus window

Class rendering uses a camera centered on the current `focus` class. All direct
neighbors in the selected view move closer temporarily. Normal focus capacity
is 5 × 5 cards on desktop, 3 × 5 on portrait mobile and 5 × 3 on landscape mobile.
Retain every direct neighbor; use smaller cards if they exceed that normal window.

At more than **20 relationships for one class within a diagram**, split the model
into coherent linked views. Keep stable class and relationship IDs. Repeat shared
classes where needed; the union of views must retain every class and relationship.
This is a readability policy, not a UML standard or an automatic code refactoring.

The regular class schema remains valid. Without `views`, the complete model is
one view and must satisfy the 20-relationship limit. For linked diagrams add:

```json
"views": [
  {"id":"purchase", "label":"Purchase & items",
   "nodes":["order","item"], "edges":["owns"]},
  {"id":"settlement", "label":"Payment & settlement",
   "nodes":["order","payment"], "edges":["paid-by"]}
]
```

Those lists must account for the complete supplied model, including classes not
shown in this abbreviated snippet. Every listed edge's endpoints belong to its
view. A walkthrough step may specify `view` and `focus`; its highlighted `nodes`
and `edges` must fit that view, and `focus` belongs to its highlighted nodes.
Without `focus`, the first highlighted node is used. Without `view`, the first
compatible view is selected. Use explicit values to make the teaching order clear.
Scenarios retain their own labels and selectable walkthroughs.

Each node retains its canonical `x`/`y` map position. Presentation does not change
the model. **View map** restores those positions. A mini-map shows the current
arrangement and camera region. Mouse/touch drag pans. Mouse wheel zooms at the
pointer; Trackpad mode uses two-finger scrolling for pan and pinch for zoom.
Shift + wheel pans in either mode. Browsers cannot reliably identify the wheel
hardware, so the scroll mode is explicit. Manual movement pauses the tour and
stops camera travel. **Resume tour** explicitly restores following.

Cards preview their first supplied attribute and operation. Long text is visually
elided to preserve readability; **Class details** contains every supplied member
and the complete description. Do not invent members when none were supplied.
Relationships retain association, composition, aggregation, inheritance or
dependency notation. Endpoint cardinalities remain in the relationship inspector
when a narrow gap cannot hold their labels. Scope, assumptions, sources and
evidence remain visible beneath the diagram.

Use the packaged renderer as usual. It emits one offline HTML and supports a
single class view or linked views without another skill or repository checkout.
Verify pan/pinch, takeover/resume, orientation changes, connector attachment,
all-neighbor retention and complete linked-view coverage. Automated mobile input
is emulation; distinguish it from physical-device and Safari acceptance.
