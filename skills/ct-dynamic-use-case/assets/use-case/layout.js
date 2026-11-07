function layout(W) {
  const small = W < 620,
    scene = {
      items: [],
      links: [],
      groups: [],
      height: 460,
      detail: null,
      title: "Choose an actor",
      hint: "Select one to reveal their use cases",
    };
  const actorX = W - (small ? 50 : 78),
    caseX = W * (small ? 0.31 : 0.36),
    caseW = Math.min(small ? 150 : 196, W * 0.48),
    groupLeft = small ? 10 : 22,
    groupWidth = actorX - (small ? 70 : 110) - groupLeft;
  function subjectBlock(a, t, y, overview = false) {
    const topic = subjects[t],
      bodyTop = y + 48,
      rowGap = Math.max(
        76,
        ...topic.cases.map((id) => nodeHeight(cases[id].name, caseW, 60) + 16),
      ),
      h = topic.cases.length * rowGap + 45;
    scene.groups.push({
      key: a + "-" + t,
      x: groupLeft,
      y,
      w: Math.max(170, groupWidth),
      h,
      label: topic.name,
      action: "subject",
      actor: a,
      value: t,
      selected: state.actor === a && state.subject === t,
    });
    topic.cases.forEach((id, i) => {
      const it = oval(
        "case-" + a + "-" + t + "-" + id,
        cases[id].name,
        caseX,
        bodyTop + 31 + i * rowGap,
        caseW,
        60,
        {
          action: "case",
          actor: a,
          subject: t,
          value: id,
          selected: state.actor === a && state.caseId === id,
        },
      );
      scene.items.push(it);
      scene.links.push(line("actor-" + a, it.key));
    });
    return y + h;
  }
  if (state.overview) {
    scene.title = "All actors and use cases";
    scene.hint = "Select a subject or an oval to focus it";
    let y = 20;
    for (const a of Object.keys(people)) {
      const start = y;
      for (const t of people[a].subjects) y = subjectBlock(a, t, y, true) + 16;
      scene.items.push(actorItem(a, actorX, (start + y - 16) / 2));
      y += 30;
    }
    scene.height = y;
    return scene;
  }
  if (!state.actor) {
    scene.items = Object.keys(people).map((a, i) =>
      actorItem(a, W / 2, 88 + i * 146),
    );
    scene.height = Math.max(320, Object.keys(people).length * 146 + 22);
    return scene;
  }
  const person = people[state.actor];
  if (!state.caseId) {
    scene.title = state.subject
      ? subjects[state.subject].name
      : person.name + " · triggering options";
    scene.hint = state.subject
      ? "Choose a use case"
      : "Choose a subject or a use case";
    let y = 20;
    for (const t of state.subject ? [state.subject] : person.subjects)
      y = subjectBlock(state.actor, t, y) + 16;
    scene.height = Math.max(350, y + 8);
    scene.items.push(actorItem(state.actor, actorX, scene.height / 2));
    return scene;
  }
  const c = cases[state.caseId];
  if (!state.scenario) {
    scene.title = c.name;
    scene.hint = "Scenario choices · select a path";
    const gap = Math.max(
      100,
      ...c.scenarios.map(
        (s) =>
          nodeHeight(s.name, small ? 175 : 178, 70, categoryNames[s.category]) +
          22,
      ),
    );
    scene.height = Math.max(415, 110 + c.scenarios.length * gap);
    const cy = scene.height / 2,
      mainX = W * (small ? 0.57 : 0.62),
      mainY = small ? 92 : cy;
    const ax = actorX,
      ay = small ? mainY : cy;
    scene.items.push(actorItem(state.actor, ax, ay));
    const main = oval(
      "case-" + state.actor + "-" + state.subject + "-" + c.id,
      c.name,
      small ? W * 0.29 : mainX,
      small ? mainY : cy,
      small ? 148 : 170,
      64,
      {
        selected: true,
        action: "case",
        actor: state.actor,
        subject: state.subject,
        value: c.id,
      },
    );
    if (small) {
      scene.height = 240 + c.scenarios.length * gap;
      scene.groups.push({
        key: "system",
        x: 10,
        y: 170,
        w: W - 20,
        h: scene.height - 185,
        label: "Scenarios · " + subjects[state.subject].name,
      });
    } else
      scene.groups.push({
        key: "system",
        x: 18,
        y: 20,
        w: W * 0.76,
        h: scene.height - 40,
        label: "Scenario choices · " + subjects[state.subject].name,
      });
    scene.items.push(main);
    scene.links.push(
      line("actor-" + state.actor, main.key, { emphasis: true }),
    );
    c.scenarios.forEach((s, i) => {
      const x = small ? W * 0.4 : W * 0.23,
        y = small
          ? 245 + i * gap
          : cy + (i - (c.scenarios.length - 1) / 2) * gap;
      const it = oval("scenario-" + s.id, s.name, x, y, small ? 175 : 178, 70, {
        kind: "scenario",
        action: "scenario",
        value: s.id,
        note: categoryNames[s.category],
      });
      scene.items.push(it);
      scene.links.push(
        line(main.key, it.key, { vertical: small, side: small }),
      );
    });
    scene.detail = {
      title: "Use case · " + c.name,
      fields: [
        ["Trigger", c.trigger],
        ["Requires", c.pre],
        ["Evidence", c.evidence.status],
      ],
    };
    return scene;
  }
  return scenarioLayout(W);
}
