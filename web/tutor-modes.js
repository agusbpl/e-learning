'use strict';
/* Modos del tutor y plan global del Margen. Sólo presentación: toda la política
   y la asignación de minutos las calcula el servidor (tutor_modes.py) y llegan
   por /api/tutor-modes. Sin azar, sin llamadas a proveedores. Si la consulta
   falla, degrada a los parciales del pliego actual y muestra un aviso, sin
   inventar fechas ni temarios. */
window.TutorModes = (() => {
  const el = (tag, attrs = {}, ...children) => {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs || {})) {
      if (value === null || value === undefined || value === false) continue;
      if (key === 'class') node.className = value;
      else if (key === 'text') node.textContent = value;
      else if (key.startsWith('on') && typeof value === 'function') node.addEventListener(key.slice(2), value);
      else node.setAttribute(key, value === true ? '' : value);
    }
    for (const child of children.flat()) if (child !== null && child !== undefined) node.append(child);
    return node;
  };
  const LABELS = { flexible: 'Flexible', strict: 'Estricto', extreme: 'Extremo' };
  const KIND = { exam: 'Parcial / examen', deadline: 'Entrega', study: 'Apuntes' };
  let cache = null;
  let refresh = null;

  async function request(body) {
    const response = await fetch('/api/tutor-modes', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || { action: 'overview' }) });
    if (!response.ok) throw new Error('No se pudo cargar el modo y el plan del Margen.');
    return response.json();
  }

  function localPlan(state) {
    const names = Object.fromEntries((state.courses || []).map(course => [course.id, course.title]));
    return (state.calendarEvents || []).filter(event => event.kind === 'exam' || event.kind === 'deadline')
      .map(event => ({ id: event.id, title: event.title, date: event.date, kind: event.kind,
                       courseTitle: names[event.courseId] || event.courseId, local: true }))
      .sort((a, b) => a.date.localeCompare(b.date));
  }

  function daysLabel(days) {
    if (days === null || days === undefined) return 'sin fecha';
    if (days < 0) return 'vencido';
    if (days === 0) return 'hoy';
    return 'en ' + days + ' día' + (days === 1 ? '' : 's');
  }

  function notice(node, payload) {
    if (!payload || !payload.notice) return;
    node.append(el('section', { class: 'tutor-modes-notice', role: 'status' },
      el('h3', { text: 'Cambio automático de modo' }),
      el('p', { text: (payload.notice.from ? 'Desde ' + LABELS[payload.notice.from] + ' a ' : '') + LABELS[payload.notice.to] + ': ' + (payload.notice.reasons || []).join(' ') }),
      el('p', { class: 'muted', text: 'Podés fijar manual o reactivar automático; la preferencia manual persiste hasta reactivar auto.' })));
  }

  function preferenceControls(container, payload, reload) {
    const preference = payload.preference || { choice: 'auto', mode: null };
    const select = el('select', { 'aria-label': 'Modo manual' },
      ...Object.entries(LABELS).map(([value, label]) => el('option', { value, selected: preference.mode === value }, label)));
    const manual = el('input', { type: 'radio', name: 'tutor-modes-choice', value: 'manual', checked: preference.choice === 'manual' });
    const auto = el('input', { type: 'radio', name: 'tutor-modes-choice', value: 'auto', checked: preference.choice === 'auto' });
    const apply = el('button', { class: 'text-button', onclick: async () => {
      try {
        await request({ action: 'setPreference', choice: auto.checked ? 'auto' : 'manual', mode: auto.checked ? '' : select.value });
        await reload();
      } catch (err) { syncMessage(err.message); }
    } }, 'Guardar preferencia');
    container.append(el('section', { class: 'tutor-modes-preference' },
      el('h3', { text: 'Exigencia del tutor' }),
      el('p', { class: 'muted', text: 'Automático usa hecho/falta y dificultad real de todas las materias del Margen; manual fija una preferencia persistente que el modo automático no reemplaza.' }),
      el('label', {}, auto, ' Automático (recomendado)'),
      el('label', {}, manual, ' Manual ', select),
      el('div', { class: 'tutor-modes-actions' }, apply)));
  }

  function planRow(entry, index, total, state, reload) {
    const controls = el('div', { class: 'tutor-modes-row-actions' },
      el('button', { class: 'text-button', disabled: index === 0, 'aria-label': 'Subir prioridad',
        onclick: () => reorder(index, index - 1) }, '↑'),
      el('button', { class: 'text-button', disabled: index === total - 1, 'aria-label': 'Bajar prioridad',
        onclick: () => reorder(index, index + 1) }, '↓'));
    const reasons = (entry.priorityReasons || []).map(reason => el('li', { text: reason }));
    const uncertainty = (entry.uncertainty || []).map(reason => el('li', { text: reason }));
    const plan = entry.plan || {};
    return el('article', { class: 'tutor-modes-row', 'data-kind': entry.kind },
      el('header', {},
        el('h4', { text: (entry.courseTitle ? entry.courseTitle + ' · ' : '') + entry.title }),
        el('small', { class: 'muted', text: (entry.date || 'sin fecha') + ' · ' + daysLabel(entry.daysLeft) + ' · ' + (KIND[entry.kind] || entry.kind) }),
        controls),
      el('p', { class: 'tutor-modes-priority', text: 'Prioridad ' + (entry.priorityScore ?? '—') + (entry.minutesAllocated !== null && entry.minutesAllocated !== undefined ? ' · ' + entry.minutesAllocated + '/' + entry.minutesRequired + ' min asignados' : '') }),
      reasons.length ? el('ul', { class: 'tutor-modes-reasons' }, ...reasons) : null,
      plan.emergency ? el('p', { class: 'tutor-modes-emergency', text: plan.note }) : null,
      plan.cover && plan.cover.length ? el('p', { class: 'muted', text: 'A cubrir: ' + plan.cover.map(l => l.title).join(', ') }) : null,
      plan.postponed && plan.postponed.length ? el('p', { class: 'tutor-modes-postponed', text: 'Queda pendiente (no acredita dominio): ' + plan.postponed.map(l => l.title).join(', ') }) : null,
      uncertainty.length ? el('ul', { class: 'tutor-modes-uncertainty' }, ...uncertainty) : null);
  }

  function move(list, from, to) {
    if (to < 0 || to >= list.length) return list;
    const copy = list.slice();
    const [item] = copy.splice(from, 1);
    copy.splice(to, 0, item);
    return copy;
  }

  async function reorder(from, to) {
    if (!cache || !cache.plan) return;
    const targets = move(cache.plan.exams.map(entry => entry.target), from, to);
    if (targets.join('|') === cache.plan.exams.map(entry => entry.target).join('|')) return;
    try {
      await request({ action: 'setPlanEdits', edits: targets });
      syncMessage('Prioridad guardada; el servidor recalcula la asignación de minutos con este orden.');
      if (refresh) await refresh();
    } catch (err) { syncMessage(err.message); }
  }

  function syncMessage(message) {
    const box = document.getElementById('tutor-modes-message');
    if (box) box.textContent = message || '';
  }

  async function mount(container, options = {}) {
    if (!container) return;
    container.replaceChildren(el('p', { class: 'muted', text: 'Cargando modos y plan del Margen…' }));
    const render = async () => {
      let payload;
      try {
        payload = await request({ action: 'overview' });
      } catch (err) {
        cache = null;
        const state = options.state || {};
        const local = localPlan(state);
        const rows = local.length
          ? local.map(entry => el('article', { class: 'tutor-modes-row' },
              el('h4', { text: (entry.courseTitle ? entry.courseTitle + ' · ' : '') + entry.title }),
              el('small', { class: 'muted', text: entry.date + ' · ' + (KIND[entry.kind] || entry.kind) })))
          : [el('p', { class: 'muted', text: 'No hay parciales ni entregas en este pliego.' })];
        container.replaceChildren(
          el('div', { class: 'eyebrow' }, 'PARCIALES DEL MARGEN'),
          el('h1', {}, 'Parciales'),
          el('p', { class: 'tutor-modes-warning', text: err.message + ' Se muestran sólo los parciales de este pliego; reintentá en unos minutos.' }),
          ...rows);
        return;
      }
      cache = payload;
      const effective = payload.effective || {};
      const decision = effective.decision || effective;
      const plan = payload.plan || {};
      const rooms = Object.values(plan.rooms || {});
      const node = el('div', { class: 'tutor-modes-panel' },
        el('div', { class: 'eyebrow' }, 'PLANIFICACIÓN GLOBAL · ' + (rooms.join(' · ') || 'Margen')),
        el('h1', {}, 'Parciales'),
        el('p', { class: 'tutor-modes-effective' },
          'Modo efectivo: ', el('strong', { text: LABELS[decision.effectiveMode] || decision.effectiveMode }),
          payload.policyVersion ? el('small', { class: 'muted', text: ' · política ' + payload.policyVersion }) : null),
        el('p', { id: 'tutor-modes-message', class: 'tutor-modes-warning', role: 'status' }));
      notice(node, effective);
      preferenceControls(node, payload, render);
      if (decision.reasons && decision.reasons.length) {
        node.append(el('details', { class: 'tutor-modes-why' }, el('summary', {}, 'Por qué este modo'),
          el('ul', {}, ...decision.reasons.map(reason => el('li', { text: reason })))));
      }
      const rows = (plan.exams || []);
      node.append(el('h2', {}, 'Compromisos ordenados por prioridad'));
      if (!rows.length) node.append(el('p', { class: 'muted', text: (plan.notes || []).join(' ') || 'Sin parciales registrados; no se inventan fechas.' }));
      rows.forEach((entry, index) => node.append(planRow(entry, index, rows.length, options.state, render)));
      if (plan.undated && plan.undated.length) {
        node.append(el('h2', {}, 'Apuntes sin fecha declarada'),
          el('ul', { class: 'tutor-modes-uncertainty' }, ...plan.undated.map(item => el('li', { text: item.title + ': ' + (item.uncertainty || []).join(' ') }))));
      }
      if (plan.notes && plan.notes.length) node.append(el('p', { class: 'muted', text: plan.notes.join(' ') }));
      container.replaceChildren(node);
    };
    refresh = render;
    await render();
    return { refresh: render };
  }

  return { mount, LABELS };
})();
