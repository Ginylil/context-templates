const root = document.getElementById("uc-diagram");
const canvas = root.querySelector(".d-canvas"),
  nodeLayer = root.querySelector(".d-nodes");
const model = JSON.parse(document.getElementById("use-case-model").textContent);
const people = model.actors,
  subjects = model.subjects,
  cases = model.use_cases;
const categoryNames = {
  main: "Main success path",
  alternative: "Alternative path",
  error: "Error path",
  recovery: "Recovery path",
};
let state = {
  actor: null,
  subject: null,
  caseId: null,
  scenario: null,
  overview: false,
};
const escape = (s) =>
  String(s).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
function restore(v) {
  const s = v?.modelContent?.diagram;
  if (!s || s.version !== 2) return;
  const a = Object.hasOwn(people, s.actor) ? s.actor : null;
  const t = a && people[a].subjects.includes(s.subject) ? s.subject : null;
  const c = t && subjects[t].cases.includes(s.caseId) ? s.caseId : null;
  const q =
    c && cases[c].scenarios.some((x) => x.id === s.scenario)
      ? s.scenario
      : null;
  state = {
    actor: a,
    subject: t,
    caseId: c,
    scenario: q,
    overview: !!v?.privateContent?.overview,
  };
}
restore(window.openai?.widgetState);
function save() {
  if (window.openai?.setWidgetState)
    window.openai
      .setWidgetState({
        modelContent: {
          diagram: {
            version: 2,
            actor: state.actor,
            subject: state.subject,
            caseId: state.caseId,
            scenario: state.scenario,
          },
          scope: model.scope,
        },
        privateContent: { overview: state.overview },
      })
      .catch(() => {});
}
let lastWidth = 0,
  rendered = false,
  edgeAnimation = 0;
const mounted = new Map();
function actorItem(id, x, y) {
  return {
    key: "actor-" + id,
    kind: "actor",
    label: people[id].name,
    x,
    y,
    w: canvas.clientWidth < 620 ? 92 : 110,
    h: 136,
    action: "actor",
    value: id,
    selected: state.actor === id,
  };
}
function nodeHeight(label, width, minimum, note = "") {
  const columns = Math.max(10, Math.floor((width - 28) / 7));
  const textHeight = Math.ceil(label.length / columns) * 17;
  const noteHeight = note ? Math.ceil(note.length / columns) * 16 + 6 : 0;
  return Math.max(minimum, textHeight + noteHeight + 26);
}
function oval(key, label, x, y, w = 170, h = 62, more = {}) {
  return {
    key,
    kind: "oval",
    label,
    x,
    y,
    w,
    h: nodeHeight(label, w, h, more.note),
    ...more,
  };
}
function line(a, b, more = {}) {
  return { a, b, ...more };
}
