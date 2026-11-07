function level(l) {
  state.overview = false;
  if (l === "root")
    state = {
      actor: null,
      subject: null,
      caseId: null,
      scenario: null,
      overview: false,
    };
  else if (l === "actor") {
    state.subject = null;
    state.caseId = null;
    state.scenario = null;
  } else if (l === "subject") {
    state.caseId = null;
    state.scenario = null;
  } else if (l === "case") state.scenario = null;
}
root.addEventListener("click", (event) => {
  const b = event.target.closest("button");
  if (!b || !root.contains(b)) return;
  if (b.dataset.action === "part") return;
  if (b.hasAttribute("data-overview")) state.overview = !state.overview;
  else if (b.dataset.recover) {
    state.scenario = b.dataset.recover;
    state.overview = false;
  } else if (b.hasAttribute("data-back")) {
    if (state.overview) state.overview = false;
    else if (state.scenario) level("case");
    else if (state.caseId) level("subject");
    else if (state.subject) level("actor");
    else level("root");
  } else if (b.dataset.level) level(b.dataset.level);
  else if (b.dataset.action === "actor") {
    state = {
      actor: b.dataset.value,
      subject: null,
      caseId: null,
      scenario: null,
      overview: false,
    };
  } else if (b.dataset.action === "subject") {
    state = {
      actor: b.dataset.actor,
      subject: b.dataset.value,
      caseId: null,
      scenario: null,
      overview: false,
    };
  } else if (b.dataset.action === "case") {
    state = {
      actor: b.dataset.actor,
      subject: b.dataset.subject,
      caseId: b.dataset.value,
      scenario: null,
      overview: false,
    };
  } else if (b.dataset.action === "scenario") {
    state.scenario = b.dataset.value;
    state.overview = false;
  } else return;
  render(true);
  save();
});
new ResizeObserver(() => {
  if (Math.abs(canvas.clientWidth - lastWidth) > 1) render();
}).observe(canvas);
window.addEventListener("openai:set_globals", (event) => {
  if (event.detail?.globals?.widgetState) {
    restore(event.detail.globals.widgetState);
    render();
  }
});
render();
