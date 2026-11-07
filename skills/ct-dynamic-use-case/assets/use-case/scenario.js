function scenarioLayout(W) {
  const small = W < 620,
    scene = { items: [], links: [], groups: [], height: 460, detail: null };
  const c = cases[state.caseId];
  const s = c.scenarios.find((s) => s.id === state.scenario),
    steps = s.steps || c.parts;
  scene.oriented = true;
  scene.title = "Scenario flow · " + s.name;
  scene.hint = categoryNames[s.category] + " · " + c.name;
  const actorLabel = people[state.actor].name;
  const flow = [
    { label: s.trigger || c.trigger, owner: actorLabel },
    ...steps.map((step) =>
      typeof step === "string"
        ? { label: step, owner: "System" }
        : { ...step, owner: step.owner === "actor" ? actorLabel : step.owner },
    ),
    { label: s.result, owner: "Outcome", outcome: true },
  ];
  const cols = small ? 1 : 2,
    rows = Math.ceil(flow.length / cols),
    stepW = small ? Math.min(250, W - 64) : Math.min(250, W * 0.36),
    stepH = Math.max(
      112,
      ...flow.map((step, i) =>
        nodeHeight(step.label, stepW, 112, i + 1 + " · " + step.owner),
      ),
    ),
    rowGap = stepH + 46;
  const top = 210;
  const startY = top + stepH / 2;
  scene.height = top + rows * rowGap;
  scene.items.push(actorItem(state.actor, small ? 50 : 78, 78));
  const main = oval(
    "case-" + state.actor + "-" + state.subject + "-" + c.id,
    c.name,
    small ? W * 0.7 : W * 0.5,
    78,
    small ? 145 : 185,
    68,
    {
      selected: true,
      action: "case",
      actor: state.actor,
      subject: state.subject,
      value: c.id,
    },
  );
  scene.items.push(main);
  scene.links.push(line("actor-" + state.actor, main.key, { emphasis: true }));
  scene.groups.push({
    key: "flow",
    x: small ? 10 : 20,
    y: 158,
    w: W - (small ? 20 : 40),
    h: scene.height - 178,
    label: "Scenario flow · " + categoryNames[s.category],
  });
  flow.forEach((step, i) => {
    const col = i % cols,
      row = Math.floor(i / cols),
      x = small ? W * 0.5 : W * (col === 0 ? 0.27 : 0.73),
      y = startY + row * rowGap;
    const it = oval("flow-" + i, step.label, x, y, stepW, stepH, {
      kind: step.outcome ? "outcome" : "action",
      action: "part",
      value: String(i),
      note: i + 1 + " · " + step.owner,
    });
    scene.items.push(it);
    scene.links.push(
      line(i ? "flow-" + (i - 1) : main.key, it.key, {
        vertical: !i || col === 0,
        emphasis: !!step.outcome,
      }),
    );
  });
  scene.detail = {
    title: "Scenario · " + s.name,
    fields: [
      ["Actor trigger", s.trigger || c.trigger],
      ["Preconditions", s.category === "recovery" ? s.condition : c.pre],
      ["Scenario condition", s.condition],
      ["Outcome", s.result],
      ["Evidence", c.evidence.status],
    ],
    recovery: s.recovery,
  };
  return scene;
}
