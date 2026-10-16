'use strict';
/**
 * Pruebas unitarias de StudyTools (web/study-tools.js).
 * Ejecutar: node tests/test_study_tools.js
 *
 * Cubren la lógica pura y el punto delicado de la integración: la metadata de
 * estudio viaja dentro del cuerpo REAL de /api/notes sin dejar el borrador de
 * notes.js desincronizado (que provocaría re-guardados en bucle).
 * La prueba de navegador integrada está en tests/browser_study_tools.cjs.
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const MODULE = fs.readFileSync(path.join(__dirname, '..', 'web', 'study-tools.js'), 'utf8');

function baseSandbox() {
  const sandbox = {
    console, setTimeout, clearTimeout,
    crypto: { randomUUID: () => 'id-' + Math.random().toString(36).slice(2) },
    Event: class { constructor(type) { this.type = type; } }
  };
  sandbox.window = sandbox;
  sandbox.Node = class {};
  sandbox.state = { courses: [], events: [], library: { notes: [], documents: [], noteTutor: [] }, settings: {} };
  sandbox.notify = () => {};
  sandbox.document = {
    getElementById: () => null,
    querySelector: () => null,
    querySelectorAll: () => [],
    createElement: () => ({ append() {}, addEventListener() {}, setAttribute() {}, remove() {} }),
    createTextNode: text => ({ textContent: text }),
    body: {}
  };
  return sandbox;
}

function load(sandbox = baseSandbox()) {
  const context = vm.createContext(sandbox);
  vm.runInContext(MODULE, context);
  return sandbox;
}

function note(over = {}) {
  return { id: 'n1', title: 'Derivadas', content: '', contentFormat: 'markdown', shared: false,
           documentId: null, page: null, anchors: [], folder: '', revision: 1, ...over };
}

let passed = 0, failed = 0;
async function test(name, fn) {
  try { await fn(); passed++; console.log(`  ok  ${name}`); }
  catch (err) { failed++; console.error(`  FAIL ${name}\n       ${err.message}`); }
}

(async () => {
  console.log('StudyTools · pruebas unitarias\n');

  const tools = () => load().StudyTools;

  console.log('Wikilinks');
  await test('extrae wikilinks y sus posiciones', () => {
    const links = tools().extractWikilinks('Mirá [[Derivadas]] y [[Regla de la cadena]].');
    assert.strictEqual(links.length, 2);
    assert.strictEqual(links[0].title, 'Derivadas');
    assert.strictEqual(links[0].index, 5);
    assert.strictEqual(links[1].title, 'Regla de la cadena');
  });
  await test('ignora wikilinks vacíos', () => {
    assert.strictEqual(tools().extractWikilinks('[[ ]] no, [[Sí]] sí').length, 1);
  });
  await test('sin wikilinks devuelve lista vacía', () => {
    assert.strictEqual(tools().extractWikilinks('texto').length, 0);
  });

  console.log('\nBúsqueda y normalización de títulos');
  await test('normaliza espacios y mayúsculas', () => {
    assert.strictEqual(tools().normalizeTitle('  Regla   DE la Cadena '), 'regla de la cadena');
  });
  await test('encuentra por título insensible a mayúsculas y espacios', () => {
    const ctx = load();
    ctx.state.library.notes = [note({ id: '1', title: 'Regla de la cadena' })];
    assert.strictEqual(ctx.StudyTools.findNoteByTitle('regla  de la cadena').id, '1');
  });
  await test('devuelve null si no existe', () => {
    assert.strictEqual(load().StudyTools.findNoteByTitle('Nada'), null);
  });

  console.log('\nReferencias inversas');
  await test('encuentra backlinks consistentes con la normalización', () => {
    const ctx = load();
    ctx.state.library.notes = [
      note({ id: '1', title: 'Derivadas', updatedAt: '2026-10-01' }),
      note({ id: '2', title: 'Integrales', content: 'Ver [[derivadas  ]]', updatedAt: '2026-10-02' }),
      note({ id: '3', title: 'Límites', content: 'sin enlaces', updatedAt: '2026-10-03' })
    ];
    const backlinks = ctx.StudyTools.getBacklinks('1');
    assert.strictEqual(backlinks.length, 1);
    assert.strictEqual(backlinks[0].note.id, '2');
  });
  await test('excluye la propia nota y ordena por fecha descendente', () => {
    const ctx = load();
    ctx.state.library.notes = [
      note({ id: '1', title: 'A', content: 'yo [[A]]' }),
      note({ id: '2', title: 'B', content: '[[A]]', updatedAt: '2026-10-05' }),
      note({ id: '3', title: 'C', content: '[[A]]', updatedAt: '2026-10-03' })
    ];
    const backlinks = ctx.StudyTools.getBacklinks('1');
    assert.deepStrictEqual(backlinks.map(b => b.note.id), ['2', '3']);
  });

  console.log('\nMenciones en material');
  await test('encuentra menciones en apuntes y ejercicios sin depender de curso', () => {
    const ctx = load();
    ctx.state.library.notes = [
      note({ id: '1', title: 'Derivadas' }),
      note({ id: '2', title: 'Resumen', content: 'Las derivadas aparecen en cinemática.' })
    ];
    ctx.state.courses = [{ id: 'c1', title: 'Física', lessons: [{ id: 'l1', title: 'MRU', blocks: [{ id: 'b1', text: 'Las derivadas de la posición.' }], exercises: [{ id: 'e1', question: '¿Qué miden las derivadas?' }] }] }];
    const mentions = ctx.StudyTools.getMentions('Derivadas');
    assert.ok(mentions.some(m => m.kind === 'apunte' && m.id === '2'));
    assert.ok(mentions.some(m => m.kind === 'clase'));
    assert.ok(mentions.some(m => m.kind === 'ejercicio'));
  });

  console.log('\nFicha de concepto');
  await test('incluye las cinco secciones y el nombre', () => {
    const card = tools().createConceptCard('Derivadas');
    for (const part of ['Definición propia', 'Ejemplo', 'Contraejemplo', 'Fuente', 'Pregunta de comprensión']) {
      assert.ok(card.includes(part), `falta ${part}`);
    }
    assert.ok(card.includes('Derivadas'));
    assert.ok(!card.includes('{concepto}'));
  });

  console.log('\nPropiedades de estudio (metadata explícita, no carpeta)');
  await test('lee materia/unidad de la metadata study', () => {
    const ctx = load();
    ctx.state.library.notes = [note({ id: '1', folder: 'Carpeta vieja', study: { materia: 'Matemática', unidad: 'U3', parcialDate: '2026-11-15', needsPractice: true, errors: [] } })];
    const props = ctx.StudyTools.getNoteProperties('1');
    assert.strictEqual(props.materia, 'Matemática');
    assert.strictEqual(props.unidad, 'U3');
    assert.strictEqual(props.parcialDate, '2026-11-15');
    assert.strictEqual(props.needsPractice, true);
  });
  await test('sin metadata devuelve campos vacíos (no inventa carpeta)', () => {
    const ctx = load();
    ctx.state.library.notes = [note({ id: '1', folder: 'Matemática / U1' })];
    const props = ctx.StudyTools.getNoteProperties('1');
    assert.strictEqual(props.materia, '');
    assert.strictEqual(props.unidad, '');
    assert.strictEqual(props.needsPractice, false);
  });

  console.log('\nFiltros');
  const twoNotes = ctx => {
    ctx.state.library.notes = [
      note({ id: '1', title: 'A', study: { materia: 'Matemática', unidad: 'U1', parcialDate: null, needsPractice: true, errors: [] } }),
      note({ id: '2', title: 'B', study: { materia: 'Física', unidad: 'U2', parcialDate: '2026-12-01', needsPractice: false, errors: [] } }),
      note({ id: '3', title: 'C' })
    ];
  };
  await test('filtros vacíos incluyen notas sin propiedades', () => {
    const ctx = load(); twoNotes(ctx);
    assert.strictEqual(ctx.StudyTools.filterNotes({}).length, 3);
  });
  await test('filtra por materia, unidad, parcial y repaso', () => {
    const ctx = load(); twoNotes(ctx);
    assert.deepStrictEqual(ctx.StudyTools.filterNotes({ materia: 'Matemática' }).map(n => n.id), ['1']);
    assert.deepStrictEqual(ctx.StudyTools.filterNotes({ unidad: 'U2' }).map(n => n.id), ['2']);
    assert.deepStrictEqual(ctx.StudyTools.filterNotes({ needsPractice: true }).map(n => n.id), ['1']);
    assert.deepStrictEqual(ctx.StudyTools.filterNotes({ parcialDate: '2026-12-01' }).map(n => n.id), ['2']);
  });
  await test('getAllMaterias/getAllUnidades ordenan y deduplican', () => {
    const ctx = load(); twoNotes(ctx);
    assert.deepStrictEqual([...ctx.StudyTools.getAllMaterias()], ['Física', 'Matemática']);
    assert.deepStrictEqual([...ctx.StudyTools.getAllUnidades()], ['U1', 'U2']);
  });

  console.log('\nGuardado real de metadata en /api/notes');
  function integrationSandbox() {
    const sandbox = baseSandbox();
    sandbox.state.library.notes = [note({ id: 'n1', title: 'Uno', content: '# Uno' })];
    const calls = [];
    sandbox.api = async (apiPath, body) => {
      calls.push({ path: apiPath, body, sent: body && body.study ? JSON.parse(JSON.stringify(body.study)) : null });
      if (apiPath !== '/api/notes') return {};
      const saved = { ...body, revision: (body.revision || 0) + 1 };
      const index = sandbox.state.library.notes.findIndex(n => n.id === saved.id);
      if (index >= 0) sandbox.state.library.notes[index] = saved; else sandbox.state.library.notes.push(saved);
      return saved;
    };
    let current = null, activeId = 'n1';
    const persist = async submitted => {
      const result = await sandbox.api('/api/notes', JSON.parse(JSON.stringify(submitted)));
      const index = sandbox.state.library.notes.findIndex(n => n.id === result.id);
      if (index >= 0) sandbox.state.library.notes[index] = result; else sandbox.state.library.notes.push(result);
      return result;
    };
    // Espeja el adaptador real: la nota activa (aunque sea nueva y sin texto) se
    // persiste por el mismo camino, sin envolver ninguna función global.
    sandbox.ClassNotes = {
      currentId: () => activeId,
      current: () => current,
      applyStudy: async (id, study) => {
        if (current && current.id === id) {
          current.study = JSON.parse(JSON.stringify(study));
          const result = await persist(current);
          current.revision = result.revision;
          current.study = result.study;
          return current.study;
        }
        const note = sandbox.state.library.notes.find(n => n.id === id);
        return (await persist({ ...JSON.parse(JSON.stringify(note)), study })).study;
      }
    };
    sandbox.__current = () => current;
    sandbox.__setCurrent = value => { current = value; };
    sandbox.__setActive = value => { activeId = value; };
    const context = vm.createContext(sandbox);
    vm.runInContext(MODULE, context);
    return { sandbox, calls };
  }

  await test('guarda la metadata de la nota activa por el adaptador, sin envolver api', async () => {
    const { sandbox, calls } = integrationSandbox();
    const originalApi = sandbox.api;
    sandbox.__setCurrent(JSON.parse(JSON.stringify(sandbox.state.library.notes[0])));
    await sandbox.StudyTools.saveStudy('n1', { materia: 'Matemática', unidad: 'U3' });
    assert.strictEqual(calls.length, 1);
    assert.strictEqual(calls[0].path, '/api/notes');
    assert.strictEqual(calls[0].sent.materia, 'Matemática');
    assert.strictEqual(calls[0].sent.unidad, 'U3');
    assert.strictEqual(sandbox.state.library.notes[0].study.materia, 'Matemática');
    assert.strictEqual(sandbox.__current().study.materia, 'Matemática', 'notes.js adopta la revisión y la metadata');
    assert.strictEqual(sandbox.window.api, originalApi, 'no se envuelve api');
  });

  await test('guarda propiedades de un apunte nuevo y sin texto al elegir la propiedad', async () => {
    const { sandbox, calls } = integrationSandbox();
    sandbox.__setCurrent({ id: 'nuevo', title: 'Apunte sin título', content: '# \n\n', contentFormat: 'markdown', shared: false, documentId: null, page: null, writingScope: 'general', pageNotes: {}, anchors: [], folder: '' });
    sandbox.__setActive('nuevo');
    await sandbox.StudyTools.saveStudy('nuevo', { needsPractice: true });
    assert.strictEqual(calls.length, 1);
    const saved = sandbox.state.library.notes.find(n => n.id === 'nuevo');
    assert.ok(saved, 'la propiedad fuerza el guardado del apunte nuevo');
    assert.strictEqual(saved.study.needsPractice, true);
  });

  await test('guarda sobre una nota no activa sin tocar la activa', async () => {
    const { sandbox } = integrationSandbox();
    sandbox.__setActive('otra');
    await sandbox.StudyTools.saveStudy('n1', { needsPractice: true });
    assert.strictEqual(sandbox.state.library.notes[0].study.needsPractice, true);
    assert.strictEqual(sandbox.state.courses.length, 0);
    assert.strictEqual(sandbox.state.events.length, 0, 'no crea feedback de curso');
  });

  await test('registra error de parcial como metadata, sin curso ni evento', async () => {
    const { sandbox } = integrationSandbox();
    sandbox.__setCurrent(JSON.parse(JSON.stringify(sandbox.state.library.notes[0])));
    await sandbox.StudyTools.logPartialError({ concept: 'Límite', errorType: 'cálculo', description: 'me equivoqué', correction: 'revisar' });
    const errors = sandbox.state.library.notes[0].study.errors;
    assert.strictEqual(errors.length, 1);
    assert.strictEqual(errors[0].concept, 'Límite');
    assert.strictEqual(sandbox.state.events.length, 0);
  });

  await test('setProperty mapea nombres heredados a la metadata', async () => {
    const { sandbox } = integrationSandbox();
    sandbox.__setCurrent(JSON.parse(JSON.stringify(sandbox.state.library.notes[0])));
    await sandbox.StudyTools.setProperty('n1', 'parcial_date', '2026-11-15');
    assert.strictEqual(sandbox.state.library.notes[0].study.parcialDate, '2026-11-15');
  });

  console.log(`\n${'-'.repeat(46)}`);
  console.log(`Resultado: ${passed} passed, ${failed} failed, ${passed + failed} total`);
  if (failed > 0) process.exit(1);
})();
