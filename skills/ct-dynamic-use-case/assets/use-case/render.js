function boundaryHtml(g) {
  return `<div class="d-boundary ${g.action ? "d-subject" : ""} ${g.selected ? "d-selected" : ""}" style="left:${g.x}px;top:${g.y}px;width:${g.w}px;height:${g.h}px">${g.action ? `<button class="d-boundary-label cursor-interaction" type="button" data-action="${g.action}" data-value="${g.value}" data-actor="${g.actor}">${escape(g.label)} ↗</button>` : `<span class="d-boundary-label">${escape(g.label)}</span>`}</div>`;
}
const personMarkup =
  '<span class="d-person" aria-hidden="true"><span class="d-headcircle"></span><span class="d-torso"></span><span class="d-arms"></span><span class="d-leg d-leg-left"></span><span class="d-leg d-leg-right"></span></span>';
function render(animate = false) {
  const W = Math.max(280, canvas.clientWidth);
  lastWidth = W;
  const scene = layout(W);
  // Reflect geometry for left-to-right exploration; text and arrow semantics stay unchanged.
  if (!scene.oriented) {
    scene.items.forEach((item) => {
      item.x = W - item.x;
    });
    scene.groups.forEach((group) => {
      group.x = W - group.x - group.w;
    });
  }
  const activeKeys = new Set(scene.items.map((i) => i.key));
  canvas.style.height = scene.height + "px";
  root.querySelector("h2").textContent = scene.title;
  root.querySelector(".d-context small").textContent = scene.hint;
  root.querySelector("[data-back]").disabled = !state.actor && !state.overview;
  root
    .querySelector("[data-overview]")
    .setAttribute("aria-pressed", String(state.overview));
  root.querySelector(".d-boundaries").innerHTML = scene.groups
    .map(boundaryHtml)
    .join("");
  for (const [key, el] of mounted)
    if (!activeKeys.has(key)) {
      el.remove();
      mounted.delete(key);
    }
  for (const it of scene.items) {
    let el = mounted.get(it.key),
      fresh = !el;
    if (!el) {
      el = document.createElement(it.action === "part" ? "div" : "button");
      if (it.action !== "part") el.type = "button";
      nodeLayer.append(el);
      mounted.set(it.key, el);
    }
    el.className =
      "d-node " +
      (it.action === "part" ? "" : "cursor-interaction ") +
      (it.kind === "actor"
        ? "d-actor"
        : it.kind === "oval"
          ? "d-oval"
          : "d-step") +
      (it.kind === "outcome" ? " d-outcome" : "") +
      (it.selected ? " d-selected" : "") +
      (fresh && animate && it.kind !== "actor" ? " d-enter" : "");
    el.style.left = it.x + "px";
    el.style.top = it.y + "px";
    el.style.width = it.w + "px";
    el.style.height = it.h + "px";
    el.dataset.action = it.action || "";
    el.dataset.value = it.value || "";
    el.dataset.actor = it.actor || "";
    el.dataset.subject = it.subject || "";
    el.dataset.node = it.key;
    el.setAttribute("aria-label", it.label + (it.note ? " · " + it.note : ""));
    el.innerHTML =
      it.kind === "actor"
        ? personMarkup + `<span class="d-actor-name">${escape(it.label)}</span>`
        : it.action === "part"
          ? `<span class="d-node-note">${escape(it.note)}</span><span>${escape(it.label)}</span>`
          : `<span>${escape(it.label)}</span>${it.note ? `<span class="d-node-note">${escape(it.note)}</span>` : ""}`;
  }
  const svg = root.querySelector(".d-edges");
  svg.setAttribute("viewBox", `0 0 ${W} ${scene.height}`);
  const animation = ++edgeAnimation;
  const until =
    performance.now() +
    (rendered && !window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? 570
      : 0);
  function drawEdges(now) {
    if (animation !== edgeAnimation) return;
    const origin = canvas.getBoundingClientRect();
    const byKey = new Map(
      scene.items.map((i) => {
        const r = mounted.get(i.key).getBoundingClientRect();
        return [
          i.key,
          {
            ...i,
            x: r.left - origin.left + r.width / 2,
            y: r.top - origin.top + r.height / 2,
            w: r.width,
            h: r.height,
          },
        ];
      }),
    );
    svg.querySelector(".d-links").innerHTML = scene.links
      .map((l) => {
        const a = byKey.get(l.a),
          b = byKey.get(l.b);
        if (!a || !b) return "";
        let sx, sy, tx, ty, d, lx, ly;
        if (l.side) {
          sx = a.x + a.w / 2;
          sy = a.y;
          tx = b.x + b.w / 2;
          ty = b.y;
          const outer = W - 18;
          d = `M${sx},${sy} C${outer},${sy} ${outer},${ty} ${tx},${ty}`;
          lx = (sx + outer) / 2 - 4;
          ly = (sy + ty) / 2;
        } else if (l.vertical) {
          const down = b.y > a.y;
          sx = a.x;
          sy = a.y + ((down ? 1 : -1) * a.h) / 2;
          tx = b.x;
          ty = b.y + ((down ? -1 : 1) * b.h) / 2;
          const mid = (sy + ty) / 2;
          d = `M${sx},${sy} C${sx},${mid} ${tx},${mid} ${tx},${ty}`;
          lx = (sx + tx) / 2 - 28;
          ly = mid;
        } else {
          const left = b.x < a.x;
          sx = a.x + (left ? -1 : 1) * (a.kind === "actor" ? 22 : a.w / 2);
          sy = a.y + (a.kind === "actor" ? -7 : 0);
          tx = b.x + (left ? 1 : -1) * (b.kind === "actor" ? 22 : b.w / 2);
          ty = b.y;
          const bend = Math.max(25, Math.abs(sx - tx) * 0.55);
          d = `M${sx},${sy} C${sx + (left ? -bend : bend)},${sy} ${tx + (left ? bend : -bend)},${ty} ${tx},${ty}`;
          lx = (sx + tx) / 2;
          ly = (sy + ty) / 2 - 7;
        }
        return `<path d="${d}" class="${l.emphasis ? "d-emphasis" : ""}" marker-end="url(#${l.emphasis ? "d-arrow" : "d-arrow-muted"})"></path>${l.label ? `<text class="d-edge-label" x="${lx}" y="${ly}" text-anchor="middle">${escape(l.label)}</text>` : ""}`;
      })
      .join("");
    if (now < until) requestAnimationFrame(drawEdges);
  }
  drawEdges(performance.now());
  const trail = [["Actors", "root"]];
  if (state.actor) trail.push([people[state.actor].name, "actor"]);
  if (state.subject) trail.push([subjects[state.subject].name, "subject"]);
  if (state.caseId) trail.push([cases[state.caseId].name, "case"]);
  if (state.scenario)
    trail.push([
      cases[state.caseId].scenarios.find((s) => s.id === state.scenario).name,
      "scenario",
    ]);
  root.querySelector(".d-trace").innerHTML =
    trail
      .map(
        ([name, level], i) =>
          `${i ? '<span class="d-chevron" aria-hidden="true">›</span>' : ""}<button class="cursor-interaction" type="button" data-level="${level}" ${i === trail.length - 1 && !state.overview ? 'aria-current="location"' : ""}>${escape(name)}</button>`,
      )
      .join("") +
    (state.overview ? '<span class="d-chevron">› Overview</span>' : "");
  const detail = root.querySelector(".d-detail");
  detail.hidden = !scene.detail;
  if (scene.detail)
    detail.innerHTML = `<div class="d-detail-title">${escape(scene.detail.title)}</div><div class="d-facts">${scene.detail.fields.map(([name, val]) => `<div><span>${escape(name)}</span>${escape(val)}</div>`).join("")}</div>${state.scenario ? `<div class="d-recovery">${scene.detail.recovery?.length ? '<span class="d-recovery-label">Recovery options</span>' : ""}${(scene.detail.recovery || []).map((r) => `<button type="button" class="d-control cursor-interaction" data-recover="${r.to}">${escape(r.label)} →</button>`).join("")}<button type="button" class="d-control cursor-interaction" data-level="case">Choose another scenario</button></div>` : ""}`;
  root.querySelector(".d-legend").textContent =
    state.caseId && !state.overview
      ? state.scenario
        ? "Scenario flow · Numbered actions → outcome"
        : "Scenario choices · Success / alternative / error / recovery"
      : "Actor → goal · Grouped by subject";
  root.querySelector(".d-live").textContent = scene.title + ". " + scene.hint;
  rendered = true;
}
