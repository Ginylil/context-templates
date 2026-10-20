# Class camera prototype

A review-only alternative class-diagram presentation. The installed UML skills,
canonical renderer and published examples retain their current behavior until
this prototype is reviewed and an integration is authorized.

The synthetic model contains 48 classes. `Order` has 27 direct relationships
overall, divided by subject across three linked diagrams with nine direct
relationships apiece. The complete edge union is preserved. Twenty relationships
per class per diagram is the prototype's decomposition limit, not a UML standard
or a claim that a production architecture was refactored.

Relationship labels avoid class interiors. Cardinality labels appear when an
endpoint gap has room; the relationship inspector always retains their full
values. Composition diamonds and inheritance triangles preserve their direction.

In Focus, a class is centered and its direct neighbors move closer. Background
classes occupy other free positions and appear during manual exploration. The
normal focus window is at most 5 × 5 on desktop, 3 × 5 on portrait mobile and
5 × 3 on landscape mobile. All direct neighbors in the selected view remain
visible; if they exceed the normal window, cards become smaller. Views above the
20-relationship limit must be decomposed rather than shrunk indefinitely.

Drag with a mouse or one/two fingers to pan. Wheel zoom is anchored at the pointer;
pinch can scale and translate simultaneously. Manual input pauses the tour and
stops camera travel. A partly complete node arrangement settles without moving
the reader's camera. **Resume tour** explicitly restores following. **View map**
restores that diagram's original coordinates; the mini-map shows the current
arrangement and visible region. Positions explain focus, not changed relationships.

Browsers expose mouse-wheel and two-finger trackpad scrolling through the same
wheel interface. The explicit **Mouse: zoom / Trackpad: pan** selector avoids a
hardware guess. Pinch zoom works in both modes; Shift + wheel also pans.
Pointer capture, cancellation and `touch-action` apply only to the diagram area.
Keyboard controls and reduced-motion behavior provide alternatives.

- [Pointer Events specification](https://www.w3.org/TR/pointerevents4/)
- [Wheel events and pinch gestures](https://developer.mozilla.org/en-US/docs/Web/API/Element/wheel_event)

Build the standalone artifact in a new ignored location:

```sh
python3 scripts/build_class_camera_demo.py --output dist/class-camera-demo/demo.html
```

Open that file manually in a browser. It includes every dependency and the
unchanged supplied logo. No application server or network is required.
The builder refuses to overwrite existing output. Do not commit the assembled HTML.
All maintained fragments stay below the repository's 300-line source limit.

The `Class camera demo` PR workflow runs layout/relationship checks and Chromium
interaction checks remotely. Its downloadable artifact contains the single HTML,
desktop/portrait/landscape screenshots, a recorded walkthrough and a proof JSON.
Automated touch input is emulation; real trackpad, phone and Safari acceptance
remain human checks. There is no staging environment. A CI artifact is a review
surface, not production publication or design acceptance.
