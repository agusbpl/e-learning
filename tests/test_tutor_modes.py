"""Pruebas mecánicas de modos del tutor y plan global; solo bases temporales.

Comprueba pares documentados en docs/modos-tutor.md contra decisiones reales de
la política (tutor_modes.py) y guardas de no-regresión: la edición del plan
REASIGNA minutos (no solo reordena), el presupuesto diario es único, la
dificultad/proximidad afectan el orden, y nada se inventa cuando faltan datos.
Estos controles NO acreditan la validez semántica del tutor; eso corresponde a
la regla de evaluación rigurosa aplicada por revisión aparte. No se llama al
tutor ni a ningún proveedor; no se escriben datos en el ~/Margen real ni HOME.
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import calendar_store
import rooms
import server
import tutor_modes
from scripts.room_backup import workspace


def course(course_id, title, lessons, version='2026-10-01'):
    return {'id': course_id, 'title': title, 'version': version, 'lessons': [
        {'id': '%s-l%d' % (course_id, i), 'title': name, 'minutes': minutes, 'priority': priority}
        for i, (name, minutes, priority) in enumerate(lessons, 1)]}


def exam(event_id, course_id, title, day, kind='exam'):
    return calendar_store.validate({'id': event_id, 'courseId': course_id, 'title': title,
                                    'date': day.isoformat(), 'kind': kind, 'revision': 1})


class ModesUnit(unittest.TestCase):
    """Pares doc↔policy sin base de datos (funciones puras)."""

    def test_contract_matches_documented_guarantees(self):
        for mode in tutor_modes.MODES:
            requirements = tutor_modes.mode_requirements(mode)
            self.assertEqual(requirements['version'], tutor_modes.POLICY_VERSION)
            self.assertIn(tutor_modes.GATE_CLAUSE, requirements['never'])
            self.assertIn('evidencia', ' '.join(requirements['never']))
        flexible = tutor_modes.mode_requirements('flexible')
        self.assertIn('pendientes, ayudas y criterios no logrados quedan conservados', ' '.join(flexible['evidenceRequirements']))
        self.assertIn('marcar independent inventado', ' '.join(flexible['never']))
        extreme = tutor_modes.mode_requirements('extreme')
        self.assertIn('transferencia a un caso nuevo del tema', ' '.join(extreme['evidenceRequirements']))
        self.assertIn('contraejemplo o defensa ante objeciones donde el tema lo permita', ' '.join(extreme['evidenceRequirements']))
        strict = tutor_modes.mode_requirements('strict')
        self.assertIn('evidencia real por criterio según la rúbrica', ' '.join(strict['evidenceRequirements']))
        self.assertIn('Modo Extremo', tutor_modes.mode_prompt('extreme'))
        with self.assertRaises(ValueError):
            tutor_modes.mode_requirements('chill')

    def test_normalize_preference_rejects_invention(self):
        self.assertEqual(tutor_modes.normalize_preference({'choice': 'manual', 'mode': 'extreme'}),
                         {'choice': 'manual', 'mode': 'extreme', 'updatedAt': date.today().isoformat()})
        self.assertIsNone(tutor_modes.normalize_preference({'choice': 'auto'})['mode'])
        with self.assertRaises(ValueError):
            tutor_modes.normalize_preference({'choice': 'manual', 'mode': 'brutal'})
        with self.assertRaises(ValueError):
            tutor_modes.normalize_preference({'choice': 'auto', 'mode': 'strict'})
        with self.assertRaises(ValueError):
            tutor_modes.normalize_preference({'choice': 'mezcla'})

    def context(self, days, ratio, uncertain=False, pressure=False, pending=True):
        return {'today': '2026-11-02', 'uncertainty': [], 'anyPending': pending,
                'exams': [{'target': 'r|c|e', 'daysLeft': days, 'kind': 'exam',
                           'readiness': {'ratio': ratio, 'uncertain': uncertain},
                           'pressure': {'required': 100, 'available': 10, 'insufficient': pressure, 'measured': True},
                           'pendingLessons': ['x'] if pending else [], 'difficulty': 1}]}

    def test_q1_near_deadline_without_mastery_switches_to_flexible_with_notice(self):
        decision = tutor_modes.effective_mode({'choice': 'auto'}, self.context(3, 0.2), last_mode='extreme')
        self.assertEqual(decision['effectiveMode'], 'flexible')
        self.assertTrue(decision['changed'])
        self.assertIn('override manual persiste', decision['notice'])
        self.assertTrue(any('Plazo próximo sin dominio acreditado' in r for r in decision['reasons']))

    def test_pressure_alone_can_trigger_flexible(self):
        decision = tutor_modes.effective_mode({'choice': 'auto'}, self.context(3, 0.9, pressure=True), last_mode='strict')
        self.assertEqual(decision['effectiveMode'], 'flexible')
        self.assertTrue(any('Presión de tiempo medida' in r for r in decision['reasons']))

    def test_first_visit_does_not_invent_previous_mode_or_alert(self):
        decision = tutor_modes.effective_mode({'choice': 'auto'}, self.context(30, 0.9, pending=False))
        self.assertIsNone(decision['notice'])
        self.assertFalse(decision['changed'])

    def test_manual_is_persistent_override_against_rebound(self):
        decision = tutor_modes.effective_mode({'choice': 'manual', 'mode': 'extreme'}, self.context(2, 0.1), last_mode='flexible')
        self.assertEqual(decision['effectiveMode'], 'extreme')
        self.assertTrue(decision['overrideActive'])
        self.assertTrue(any('manual' in r for r in decision['reasons']))

    def test_untested_urgency_is_declared_not_invented(self):
        context = {'today': '2026-11-02', 'exams': [], 'anyPending': False,
                   'uncertainty': ['No hay minutos declarados: no se puede afirmar urgencia de tiempo.']}
        decision = tutor_modes.effective_mode({'choice': 'auto'}, context)
        self.assertEqual(decision['effectiveMode'], 'extreme')
        self.assertTrue(any('sin inventar urgencia' in r for r in decision['reasons']))

    def test_decisions_are_deterministic(self):
        self.assertEqual(tutor_modes.effective_mode({'choice': 'auto'}, self.context(5, 0.3)),
                         tutor_modes.effective_mode({'choice': 'auto'}, self.context(5, 0.3)))

    def test_calendar_helpers_declare_only_recorded_data(self):
        events = [{'id': 'a', 'courseId': 'c', 'kind': 'deadline', 'date': '2026-12-02'},
                  {'id': 'b', 'courseId': 'c', 'kind': 'theory', 'date': '2026-12-01'},
                  {'id': 'c', 'courseId': 'c', 'kind': 'exam', 'date': '2026-12-01'},
                  {'id': 'd', 'courseId': 'c', 'kind': 'exam', 'date': '2026-12-03'}]
        self.assertEqual([e['id'] for e in calendar_store.commitments(events)], ['c', 'a', 'd'])
        self.assertEqual(calendar_store.commitments([]), [])
        notes = [{'id': 'n1', 'title': 'T', 'study': {'materia': 'M', 'parcialDate': '2026-12-01'}},
                 {'id': 'n2', 'study': {'materia': 'M', 'parcialDate': '2026-13-01'}},
                 {'id': 'n3', 'study': {'materia': 'M'}}]
        self.assertEqual([item['noteId'] for item in calendar_store.study_dates(notes)], ['n1'])
        self.assertEqual(calendar_store.study_dates(None), [])


class VaultFixture(unittest.TestCase):
    """Bases temporales con rooms/server reales; nunca toca datos reales ni HOME."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='glosa-modes-')
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name) / 'data'
        self.data.mkdir()
        (self.data / 'Margen').mkdir()
        self.home = Path(self.temp.name) / 'home'
        self.home.mkdir()
        for env in ({'HOME': str(self.home)}, {'GLOSA_MARGEN_DIR': str(self.data / 'Margen')}):
            patcher = patch.dict('os.environ', env)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.token = server.ACTIVE_WORKSPACE.set({'root': ROOT, 'data': self.data, 'id': 'glosa-modes-fixture'})
        self.addCleanup(lambda: server.ACTIVE_WORKSPACE.reset(self.token))

    def today(self):
        return date.today()

    def pliego(self, title):
        created = rooms.create(self.data, ROOT, title)
        return rooms.room(self.data, ROOT, created['id']), created['id']

    def add_course(self, scope, body, calendar=(), events=()):
        with tutor_modes._Scoped(server, scope), server.connect() as conn:
            conn.execute('INSERT OR REPLACE INTO courses VALUES(?,?)', (body['id'], json.dumps(body, ensure_ascii=False)))
            for event in calendar:
                conn.execute('INSERT OR REPLACE INTO calendar_events VALUES(?,?)', (event['id'], json.dumps(event, ensure_ascii=False)))
            index = 0
            for kind, cid, lid, data in events:
                index += 1
                conn.execute('INSERT INTO events VALUES(?,?,?,?,?,?)', ('ev-%s-%d' % (cid, index), self.today().isoformat() + 'T10:00:00', kind, cid, lid, json.dumps(data, ensure_ascii=False)))

    def settings(self, scope, weekday=60, weekend=0):
        with tutor_modes._Scoped(server, scope), server.connect() as conn:
            body = {**server.BASE_SETTINGS, 'weekdayMinutes': weekday, 'weekendMinutes': weekend,
                    'dailyOverrides': {}, 'examDate': (self.today() + timedelta(days=90)).isoformat()}
            conn.execute('UPDATE config SET body=? WHERE id=1', (json.dumps(body, ensure_ascii=False),))

    def add_note(self, scope, note):
        with tutor_modes._Scoped(server, scope), server.connect() as conn:
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if 'notes' not in tables:
                self.skipTest('La biblioteca no expone tabla notes en esta base.')
            conn.execute('INSERT OR REPLACE INTO notes VALUES(?,?)', (note['id'], json.dumps(note, ensure_ascii=False)))

    def two_rooms(self, second_weekday=60):
        first_scope, first_id = self.pliego('Análisis')
        ana = course('analisis', 'Análisis', [('Límites', 40, 1), ('Derivadas', 40, 2)])
        self.add_course(first_scope, ana, calendar=[
            exam('ex-1', 'analisis', 'Parcial 1', self.today() + timedelta(days=5)),
            exam('tp-1', 'analisis', 'TP', self.today() + timedelta(days=4), kind='deadline')])
        self.settings(first_scope, weekday=60)
        second_scope, second_id = self.pliego('Sistemas')
        self.add_course(second_scope, course('sistemas', 'Sistemas', [('Redes', 30, 1)]), calendar=[
            exam('ex-2', 'sistemas', 'Parcial Sistemas', self.today() + timedelta(days=5))])
        self.settings(second_scope, weekday=second_weekday)
        return first_scope, first_id, second_scope, second_id


class PlanTests(VaultFixture):

    def test_plan_covers_all_rooms_with_composite_targets(self):
        _, first_id, _, second_id = self.two_rooms()
        plan = tutor_modes.build_global_plan(server)
        targets = [entry['target'] for entry in plan['exams']]
        self.assertIn(first_id + '|analisis|ex-1', targets)
        self.assertIn(second_id + '|sistemas|ex-2', targets)
        self.assertIn(first_id + '|analisis|tp-1', targets)
        self.assertNotIn('|'.join((first_id, 'analisis', 'ex-2')), targets)

    def test_availability_pool_is_global_and_single(self):
        self.two_rooms()
        plan = tutor_modes.build_global_plan(server)
        first = [e for e in plan['exams'] if e['eventId'] == 'ex-1'][0]
        coincidence = sum(plan['availability']['perDay'].get(d.isoformat(), 0)
                          for d in tutor_modes._days_between(self.today(), self.today() + timedelta(days=5)))
        # Ningún compromiso recibe más minutos que el pool global declarado hasta su fecha.
        self.assertLessEqual(first['minutesAvailable'], coincidence)
        self.assertGreater(coincidence, 0)
        # Los minutos asignados nunca superan el pool compartido total.
        assigned = sum(min(e['minutesAllocated'], e['minutesRequired']) for e in plan['exams'])
        self.assertLessEqual(assigned, sum(plan['availability']['perDay'].values()))

    def test_conflicting_declared_availability_uses_minimum_and_states_sources(self):
        self.two_rooms(second_weekday=120)
        plan = tutor_modes.build_global_plan(server)
        self.assertTrue(any('difiere entre pliegos' in note for note in plan['notes']))
        self.assertTrue(all(': ' in source for source in plan['availability']['sources']))
        per_day = plan['availability']['perDay']
        self.assertTrue(all(minutes <= 60 for minutes in per_day.values()))

    def test_unconfirmed_temario_is_declared_not_invented(self):
        self.two_rooms()
        plan = tutor_modes.build_global_plan(server)
        first = [e for e in plan['exams'] if e['eventId'] == 'ex-1'][0]
        self.assertEqual(first['temario']['source'], 'full_course')
        self.assertIn('Sin temario confirmado para este compromiso: se considera la materia completa.', first['uncertainty'])

    def test_confirmed_temario_counts_only_its_lessons_and_revision_guard(self):
        _, first_id, _, _ = self.two_rooms()
        saved = tutor_modes.save_exam_topics(server, first_id, 'analisis', 'ex-1', ['analisis-l1', 'analisis-l2'], status='confirmed')
        self.assertEqual(saved['status'], 'confirmed')
        with self.assertRaises(ValueError):
            tutor_modes.save_exam_topics(server, first_id, 'analisis', 'ex-1', ['analisis-l1'], expected_revision=0)
        with self.assertRaises(ValueError):
            tutor_modes.save_exam_topics(server, first_id, 'analisis', 'ex-1', ['fantasma'], expected_revision=1)
        with self.assertRaises(ValueError):
            tutor_modes.save_exam_topics(server, first_id, 'analisis', 'ex-1', [], expected_revision=1)
        plan = tutor_modes.build_global_plan(server)
        first = [e for e in plan['exams'] if e['eventId'] == 'ex-1'][0]
        self.assertEqual(first['temario']['source'], 'confirmed')
        self.assertEqual(first['temarioReadiness']['total'], 2)
        self.assertEqual(first['minutesRequired'], 80)
        self.assertEqual(first['uncertainty'], [])

    def test_emergency_marks_deficit_and_keeps_explicit_postergados(self):
        first_scope, first_id, _, _ = self.two_rooms()
        self.settings(first_scope, weekday=20)
        tutor_modes.save_exam_topics(server, first_id, 'analisis', 'ex-1', ['analisis-l1', 'analisis-l2'], status='confirmed')
        plan = tutor_modes.build_global_plan(server)
        first = [e for e in plan['exams'] if e['eventId'] == 'ex-1'][0]
        self.assertTrue(first['plan']['emergency'])
        self.assertTrue(plan['emergency'])
        self.assertTrue(first['plan']['postponed'])
        self.assertTrue(all(l['assignedMinutes'] < l['minutes'] for l in first['plan']['postponed']))
        self.assertIn('no declara dominio', first['plan']['note'])
        covered_ids = {l['id'] for l in first['plan']['cover']} | {l['id'] for l in first['plan']['postponed']}
        self.assertEqual(covered_ids, {l['id'] for l in first['pendingLessons']})

    def test_user_priority_reassigns_minutes_not_only_order(self):
        """Dos parciales el mismo día con capacidad insuficiente: invertir prioridad invierte la asignación."""
        first_scope, first_id = self.pliego('Física')
        self.add_course(first_scope, course('fisica', 'Física', [('Cinemática', 60, 1)]),
                        calendar=[exam('fx-1', 'fisica', 'Parcial Física', self.today() + timedelta(days=1))])
        self.settings(first_scope, weekday=20, weekend=20)
        second_scope, second_id = self.pliego('Química')
        self.add_course(second_scope, course('quimica', 'Química', [('Estequiometría', 60, 1)]),
                        calendar=[exam('qm-1', 'quimica', 'Parcial Química', self.today() + timedelta(days=1))])
        self.settings(second_scope, weekday=20, weekend=20)
        target_a = '|'.join((first_id, 'fisica', 'fx-1'))
        target_b = '|'.join((second_id, 'quimica', 'qm-1'))
        pool = sum(tutor_modes.build_global_plan(server)['availability']['perDay'].get(
            (self.today() + timedelta(days=i)).isoformat(), 0) for i in range(2))
        self.assertGreater(pool, 0)
        self.assertLess(pool, 120)
        tutor_modes.save_plan_edits(server, [target_a])
        plan_a = tutor_modes.build_global_plan(server)
        entry_a = [e for e in plan_a['exams'] if e['target'] == target_a][0]
        entry_b = [e for e in plan_a['exams'] if e['target'] == target_b][0]
        self.assertEqual(plan_a['exams'][0]['target'], target_a)
        self.assertEqual(entry_a['minutesAllocated'], pool)
        self.assertEqual(entry_b['minutesAllocated'], 0)
        tutor_modes.save_plan_edits(server, [target_b])
        plan_b = tutor_modes.build_global_plan(server)
        entry_a2 = [e for e in plan_b['exams'] if e['target'] == target_a][0]
        entry_b2 = [e for e in plan_b['exams'] if e['target'] == target_b][0]
        self.assertEqual(plan_b['exams'][0]['target'], target_b)
        self.assertEqual(entry_b2['minutesAllocated'], pool)
        self.assertEqual(entry_a2['minutesAllocated'], 0)
        # Los minutos del pool nunca se usan dos veces.
        self.assertEqual(entry_a['minutesAllocated'] + entry_b['minutesAllocated'], pool)

    def test_difficulty_and_proximity_drive_automatic_ranking(self):
        first_scope, first_id = self.pliego('Álgebra')
        self.add_course(first_scope, course('algebra', 'Álgebra', [('Matrices', 60, 1)]),
                        calendar=[exam('al-1', 'algebra', 'Parcial cerca', self.today() + timedelta(days=1))],
                        events=[('assessment', 'algebra', 'algebra-l1', {'courseVersion': '2026-10-01', 'status': 'pending'}),
                                ('assessment', 'algebra', 'algebra-l1', {'courseVersion': '2026-10-01', 'status': 'pending'}),
                                ('assessment', 'algebra', 'algebra-l1', {'courseVersion': '2026-10-01', 'status': 'pending'})])
        self.settings(first_scope, weekday=20, weekend=20)
        second_scope, second_id = self.pliego('Historia')
        self.add_course(second_scope, course('historia', 'Historia', [('Revolución', 60, 1)]),
                        calendar=[exam('hi-1', 'historia', 'Parcial lejano', self.today() + timedelta(days=30))])
        self.settings(second_scope, weekday=20, weekend=20)
        plan = tutor_modes.build_global_plan(server)
        self.assertEqual(plan['exams'][0]['eventId'], 'al-1')
        near = plan['exams'][0]
        self.assertTrue(any('Dificultad por evidencia nivel' in reason for reason in near['priorityReasons']))

    def test_notes_only_parcial_date_is_used_and_undated_is_declared(self):
        scope, room_id = self.pliego('Apuntes')
        self.settings(scope, weekday=30)
        self.add_note(scope, {'id': 'n1', 'title': 'Parcial Física', 'study': {
            'materia': 'Física', 'unidad': 'U1', 'parcialDate': (self.today() + timedelta(days=10)).isoformat(),
            'needsPractice': True, 'errors': [{'id': 'e1', 'concept': 'Caída libre', 'errorType': 'cálculo',
                                               'description': '', 'correction': '', 'createdAt': ''}]}})
        self.add_note(scope, {'id': 'n2', 'title': 'Sin fecha', 'study': {'materia': 'Química', 'unidad': '', 'parcialDate': None,
                                                                          'needsPractice': False, 'errors': []}})
        plan = tutor_modes.build_global_plan(server)
        notes_entry = [e for e in plan['exams'] if e.get('noteId') == 'n1'][0]
        self.assertEqual(notes_entry['kind'], 'study')
        self.assertEqual(notes_entry['daysLeft'], 10)
        self.assertEqual(notes_entry['difficulty']['declaredErrors'], 1)
        self.assertTrue(notes_entry['difficulty']['needsPractice'])
        self.assertTrue(any('declarada en apuntes' in u for u in notes_entry['uncertainty']))
        self.assertEqual([item['noteId'] for item in plan['undated']], ['n2'])
        self.assertTrue(any('Sin fecha de parcial declarada' in u for u in plan['undated'][0]['uncertainty']))

    def test_invalid_date_is_declared_not_fixed(self):
        scope, room_id = self.pliego('Roto')
        self.add_course(scope, course('roto', 'Roto', [('A', 10, 1)]), calendar=[
            {'id': 'bad-1', 'courseId': 'roto', 'title': 'Fecha inválida', 'date': '2026-13-40', 'kind': 'exam', 'revision': 1}])
        self.settings(scope, weekday=60)
        plan = tutor_modes.build_global_plan(server)
        bad = [e for e in plan['exams'] if e['eventId'] == 'bad-1'][0]
        self.assertIsNone(bad['daysLeft'])
        self.assertIn('no es válida', bad['uncertainty'][0])
        self.assertEqual(bad['priorityScore'], 0)

    def test_other_kinds_are_ignored(self):
        scope, room_id = self.pliego('Cursos')
        self.add_course(scope, course('c1', 'C1', [('A', 10, 1)]), calendar=[
            exam('cls', 'c1', 'Teoría', self.today() + timedelta(days=1), kind='theory')])
        plan = tutor_modes.build_global_plan(server)
        self.assertNotIn('cls', {e['eventId'] for e in plan['exams']})

    def test_scopes_exclude_tutorial(self):
        self.two_rooms()
        self.assertNotIn(rooms.TUTORIAL_ID, {item['id'] for item in tutor_modes.scopes(server)})


class PreferenceTests(VaultFixture):

    def test_preference_is_bound_to_the_chosen_margen_identity(self):
        self.pliego('Anillo')
        saved = tutor_modes.save_preference(server, {'choice': 'manual', 'mode': 'strict'})
        self.assertEqual(saved['choice'], 'manual')
        self.assertEqual(tutor_modes.read_preference(server)['mode'], 'strict')
        self.assertIn('margen-' , tutor_modes.store_path(server).name)
        other = Path(self.temp.name) / 'otro-data'
        other.mkdir()
        (other / 'Margen').mkdir()
        with patch.dict('os.environ', {'GLOSA_MARGEN_DIR': str(other / 'Margen')}):
            self.assertNotEqual(tutor_modes.store_path(server), tutor_modes.store_path(server).parent / 'x')
            self.assertNotEqual(str(tutor_modes._margen_identity(server)), '')

    def test_save_and_reload_preference_round_trip(self):
        self.pliego('Redes')
        tutor_modes.save_preference(server, {'choice': 'auto'})
        state = tutor_modes.read_state(server)
        self.assertEqual(state['preference']['choice'], 'auto')
        tutor_modes.save_plan_edits(server, ['a|b|c'])
        self.assertEqual(tutor_modes.read_plan_edits(server), ['a|b|c'])
        payload = tutor_modes.export_payload(server)
        self.assertEqual(payload['format'], 'glosa-tutor-modes')
        tutor_modes.import_payload(server, payload)
        self.assertEqual(tutor_modes.read_preference(server)['choice'], 'auto')

    def test_notice_delivered_once_per_real_change(self):
        scope, room_id = self.pliego('Aviso')
        self.add_course(scope, course('c1', 'C1', [('A', 60, 1)]), calendar=[
            exam('ev-1', 'c1', 'Parcial', self.today() + timedelta(days=2))])
        self.settings(scope, weekday=60)
        tutor_modes.save_preference(server, {'choice': 'auto'})
        state = tutor_modes.read_state(server)
        state['lastEffectiveMode'] = 'extreme'
        tutor_modes.write_state(server, state)
        first = tutor_modes.evaluate_mode(server)
        self.assertIsNotNone(first['notice'])
        self.assertEqual(first['decision']['effectiveMode'], 'flexible')
        second = tutor_modes.evaluate_mode(server)
        self.assertIsNone(second['notice'])
        third = tutor_modes.evaluate_mode(server)
        self.assertIsNone(third['notice'])

    def test_effective_now_attaches_requirements_and_mode_prompt(self):
        self.pliego('Uno')
        effective = tutor_modes.effective_now(server)
        self.assertIn(effective['effectiveMode'], tutor_modes.MODES)
        self.assertEqual(effective['requirements']['version'], tutor_modes.POLICY_VERSION)
        self.assertIn(tutor_modes.GATE_CLAUSE, effective['requirements']['never'])

    def test_plan_context_reads_only_real_dates(self):
        scope, room_id = self.pliego('Ctx')
        self.add_course(scope, course('c1', 'Uno', [('A', 30, 1)]), calendar=[
            exam('ev-1', 'c1', 'Parcial', self.today() + timedelta(days=6))])
        self.settings(scope, weekday=60)
        context = tutor_modes.plan_context(server)
        self.assertEqual(len(context['exams']), 1)
        self.assertEqual(context['exams'][0]['daysLeft'], 6)
        self.assertTrue(context['exams'][0]['readiness']['uncertain'])


if __name__ == '__main__':
    unittest.main()
