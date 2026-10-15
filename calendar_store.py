"""Course calendar shared by the UI and authoring MCP, with revision checks."""
from datetime import date, time
import json
import uuid

KINDS={'theory','practice','deadline','exam','study'}


def validate(event):
    if not isinstance(event, dict): raise ValueError('Evento de calendario inválido.')
    for field in ('id','courseId','title','date','kind'):
        if not isinstance(event.get(field),str) or not event[field].strip():raise ValueError('Falta '+field+' en el evento.')
    if len(event['title'])>200 or len(event['id'])>200 or event['kind'] not in KINDS:raise ValueError('Título o tipo de evento inválido.')
    start=date.fromisoformat(event['date'])
    if event['date']!=start.isoformat():raise ValueError('La fecha debe usar YYYY-MM-DD.')
    if event.get('time'):
        clock=time.fromisoformat(event['time'])
        if event['time']!=clock.strftime('%H:%M'):raise ValueError('La hora debe usar HH:MM.')
    if event.get('repeatUntil'):
        end=date.fromisoformat(event['repeatUntil'])
        if event['repeatUntil']!=end.isoformat():raise ValueError('La fecha final debe usar YYYY-MM-DD.')
        if end<start or (end-start).days>730:raise ValueError('La repetición semanal debe terminar dentro de dos años.')
    if type(event.get('revision')) is not int or event['revision']<1:raise ValueError('Revisión inválida.')
    return {k:event.get(k,'') for k in ('id','courseId','title','date','kind','time','repeatUntil','revision')}


def save(server, body, expected_revision=0):
    if not isinstance(body,dict) or type(expected_revision) is not int or expected_revision<0:raise ValueError('Evento o revisión esperada inválidos.')
    candidate=validate({**body,'id':body.get('id') or str(uuid.uuid4()),'revision':expected_revision+1})
    with server.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        if not conn.execute('SELECT 1 FROM courses WHERE id=?',(candidate['courseId'],)).fetchone():raise ValueError('Curso inexistente.')
        old=conn.execute('SELECT body FROM calendar_events WHERE id=?',(candidate['id'],)).fetchone()
        previous=json.loads(old['body']) if old else None
        if (previous['revision'] if previous else 0)!=expected_revision:raise ValueError('El evento cambió. Recargá antes de editar.')
        if previous and previous['courseId']!=candidate['courseId']:raise ValueError('No cambies la cursada de un evento al editarlo.')
        conn.execute('INSERT OR REPLACE INTO calendar_events VALUES(?,?)',(candidate['id'],json.dumps(candidate,ensure_ascii=False)))
    return candidate


def delete(server, event_id, expected_revision):
    if type(expected_revision) is not int or expected_revision<1:raise ValueError('Revisión esperada inválida.')
    with server.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        old=conn.execute('SELECT body FROM calendar_events WHERE id=?',(event_id,)).fetchone()
        if not old or json.loads(old['body'])['revision']!=expected_revision:raise ValueError('El evento cambió o ya no existe.')
        conn.execute('DELETE FROM calendar_events WHERE id=?',(event_id,))
    return {'deleted':True}
