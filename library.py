"""Local class notes, optional documents and course drafts shared by UI and MCP."""
from datetime import datetime, timezone
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import uuid


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def note_markdown(note, documents):
    """One readable Markdown document; pageNotes remains the lossless page index."""
    titles={d['id']:d['title'] for d in documents}
    sections=[note['content']] if note.get('contentFormat') == 'markdown' else ['# '+note['title'],note['content']]
    for doc_id,pages in note.get('pageNotes',{}).items():
        sections.append('## Fuente: '+titles.get(doc_id,doc_id))
        pages={'1':'',**pages}
        for page,text in sorted(pages.items(),key=lambda pair:int(pair[0])):
            sections.append('#'+page+'\n\n'+text)
    for anchor in note.get('anchors',[]):
        sections.append('## '+('Anotación independiente' if anchor.get('scope')=='general' else 'Anotación · pag'+str(anchor['page']))+'\n\n'+('> '+anchor['quote'].replace('\n','\n> ')+'\n\n' if anchor.get('quote') else '')+anchor.get('comment',''))
    return '\n\n'.join(s for s in sections if s)+'\n'


class Library:
    def __init__(self, db, data, root):
        self.db, self.data, self.root = Path(db), Path(data), Path(root)

    def connect(self):
        conn = sqlite3.connect(self.db, timeout=20)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self, courses):
        with self.connect() as conn:
            conn.executescript('''
            CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS notes(id TEXT PRIMARY KEY, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS note_versions(id TEXT NOT NULL, revision INTEGER NOT NULL, body TEXT NOT NULL, PRIMARY KEY(id,revision));
            CREATE TABLE IF NOT EXISTS course_drafts(id TEXT PRIMARY KEY, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS note_tutor(id TEXT PRIMARY KEY, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tutor_contexts(id TEXT PRIMARY KEY, body TEXT NOT NULL);
            ''')
            for course in courses:
                for source in course.get('sources', []):
                    if not source.get('url', '').startswith('/sources/'):
                        continue
                    filename = Path(source['url']).name
                    path = self.root / 'sources' / filename
                    if not path.is_file() or path.suffix.lower() != '.pdf':
                        continue
                    body = {'id': source['id'], 'title': source['title'], 'sha256': source.get('sha256') or hashlib.sha256(path.read_bytes()).hexdigest(), 'pages': source.get('pages'), 'storage': 'source', 'filename': filename, 'createdAt': timestamp()}
                    conn.execute('INSERT OR IGNORE INTO documents VALUES(?,?)', (body['id'], json.dumps(body, ensure_ascii=False)))

    def snapshot(self):
        with self.connect() as conn:
            data={key: [json.loads(row['body']) for row in conn.execute('SELECT body FROM '+table+' ORDER BY rowid')] for key, table in [('documents','documents'), ('notes','notes'), ('noteVersions','note_versions'), ('courseDrafts','course_drafts'), ('noteTutor','note_tutor'), ('tutorContexts','tutor_contexts')]}
        data['deletedNotes']=[n for n in data['notes'] if n.get('deletedAt')]
        data['notes']=[n for n in data['notes'] if not n.get('deletedAt')]
        return data

    def document(self, document_id):
        with self.connect() as conn:
            row = conn.execute('SELECT body FROM documents WHERE id=?', (document_id,)).fetchone()
        if not row:
            raise ValueError('Documento inexistente.')
        return json.loads(row['body'])

    def document_path(self, document):
        directory = self.root/'sources' if document['storage']=='source' else self.data/'documents'
        filename = document['filename']
        if Path(filename).name != filename or not filename.endswith('.pdf'):
            raise ValueError('Referencia de documento inválida.')
        return directory/filename

    def pages(self, document_id, start=1, end=None):
        doc = self.document(document_id)
        end = start if end is None else end
        if type(start) is not int or type(end) is not int or start<1 or end<start or end-start>=20:
            raise ValueError('Pedí entre 1 y 20 páginas por consulta.')
        cache = (self.root/'.md_cache'/(document_id+'.json') if doc['storage']=='source' else self.data/'documents'/(document_id+'.json'))
        if not cache.is_file():
            return {'document': doc, 'pages': [], 'warning': 'No hay texto extraído. El agente puede leer el PDF original; un escaneo podría requerir OCR.'}
        data = json.loads(cache.read_text())
        return {'document': doc, 'pages': [p for p in data['pages'] if start<=p['page']<=end]}

    def upload(self, title, encoded):
        if not isinstance(title,str) or not title.strip() or len(title)>200:
            raise ValueError('Indicá un título de documento de hasta 200 caracteres.')
        if not isinstance(encoded,str): raise ValueError('Archivo inválido.')
        try: raw = base64.b64decode(encoded, validate=True)
        except ValueError: raise ValueError('Archivo inválido.') from None
        if not 1<=len(raw)<=20_000_000 or not raw.lstrip().startswith(b'%PDF-'):
            raise ValueError('Adjuntá un PDF de hasta 20 MB.')
        sha = hashlib.sha256(raw).hexdigest()
        with self.connect() as conn:
            for row in conn.execute('SELECT body FROM documents'):
                old=json.loads(row['body'])
                if old['sha256']==sha: return old
        document_id='doc-'+sha[:24]
        directory=self.data/'documents';directory.mkdir(parents=True,exist_ok=True)
        path=directory/(document_id+'.pdf');path.write_bytes(raw)
        cache=directory/(document_id+'.json')
        helper=self.root/'scripts'/'extract_document.py'
        runtime=self.root/'.venv-author'/'bin'/'python'
        try:
            result=subprocess.run([str(runtime),str(helper),str(path),str(cache)],capture_output=True,text=True,timeout=120)
            if result.returncode: raise ValueError('No se pudo leer el PDF. Probá un archivo sin contraseña y verificá que no esté dañado.')
            pages=json.loads(cache.read_text())['pages']
        except (OSError,subprocess.TimeoutExpired):
            raise ValueError('No se pudo preparar el PDF. Revisá el runtime de documentos en las instrucciones.') from None
        doc={'id':document_id,'title':title.strip(),'sha256':sha,'pages':len(pages),'storage':'upload','filename':path.name,'createdAt':timestamp()}
        with self.connect() as conn:
            conn.execute('INSERT OR IGNORE INTO documents VALUES(?,?)',(document_id,json.dumps(doc,ensure_ascii=False)))
        return self.document(document_id)

    def validate_note(self, note, document_ids=None):
        if not isinstance(note,dict): raise ValueError('Nota inválida.')
        for field,limit in [('title',200),('folder',120),('content',200000)]:
            if not isinstance(note.get(field),str) or len(note[field])>limit:
                raise ValueError('Campo de nota inválido: '+field)
        if not note['title'].strip(): raise ValueError('La nota necesita título.')
        if type(note.get('shared')) is not bool: raise ValueError('Indicá si la nota se comparte con el agente autor.')
        documents={d['id']:d for d in self.snapshot()['documents']} if document_ids is None else document_ids
        doc_id=note.get('documentId')
        if doc_id is not None and doc_id not in documents: raise ValueError('El documento adjunto no existe.')
        page=note.get('page')
        if page is not None and (doc_id is None or type(page) is not int or page<1 or (documents[doc_id].get('pages') and page>documents[doc_id]['pages'])):
            raise ValueError('Página de nota inválida.')
        writing_scope=note.get('writingScope','general')
        if writing_scope not in ('general','page') or (writing_scope=='page' and doc_id is None):
            raise ValueError('Elegí apunte general o por página con un PDF adjunto.')
        page_notes=note.get('pageNotes',{})
        if not isinstance(page_notes,dict): raise ValueError('Apuntes por página inválidos.')
        entries=0;characters=len(note['content'])
        for source_id,notes in page_notes.items():
            if source_id not in documents or not isinstance(notes,dict): raise ValueError('Documento de apuntes por página inválido.')
            for key,text in notes.items():
                if not isinstance(key,str) or not re.fullmatch(r'[1-9][0-9]{0,6}',key) or (documents[source_id].get('pages') and int(key)>documents[source_id]['pages']):
                    raise ValueError('Página de apunte inválida.')
                if not isinstance(text,str) or len(text)>200000: raise ValueError('Texto de apunte por página inválido.')
                entries+=1;characters+=len(text)
        if entries>1000 or characters>2000000: raise ValueError('El apunte supera el límite de páginas o texto.')
        if writing_scope=='page':
            page_notes={source_id:dict(pages) for source_id,pages in page_notes.items()}
            page_notes.setdefault(doc_id,{}).setdefault('1','')
        anchors=note.get('anchors',[])
        if not isinstance(anchors,list) or len(anchors)>1000: raise ValueError('Referencias de nota inválidas.')
        for a in anchors:
            if not isinstance(a,dict) or a.get('scope','page') not in ('page','general') or not isinstance(a.get('quote'),str) or len(a['quote'])>20000:
                raise ValueError('Fragmento de fuente inválido.')
            if a.get('documentId') is None:
                if a.get('scope','page')!='general' or a.get('page') is not None or a.get('sha256') is not None:
                    raise ValueError('Una anotación de página necesita una fuente válida.')
            else:
                if a.get('documentId') not in documents or type(a.get('page')) is not int or a['page']<1 or (documents[a['documentId']].get('pages') and a['page']>documents[a['documentId']]['pages']):
                    raise ValueError('Fragmento de fuente inválido.')
                if a.get('sha256')!=documents[a['documentId']]['sha256']: raise ValueError('La versión del documento no coincide.')
            if not isinstance(a.get('comment',''),str) or len(a.get('comment',''))>20000: raise ValueError('Comentario de fuente inválido.')
            if 'selector' in a:
                selector=a['selector']
                if not isinstance(selector,dict) or type(selector.get('start')) is not int or type(selector.get('end')) is not int or not 0<=selector['start']<selector['end']<=5000000:
                    raise ValueError('Posición de resaltado inválida.')
            if 'rects' in a:
                if not isinstance(a['rects'],list) or not 1<=len(a['rects'])<=1000: raise ValueError('Resaltado de PDF inválido.')
                for rect in a['rects']:
                    if not isinstance(rect,dict) or any(type(rect.get(k)) not in (int,float) or not math.isfinite(rect[k]) or not 0<=rect[k]<=1 for k in ('x','y','width','height')) or rect['width']<=0 or rect['height']<=0 or rect['x']+rect['width']>1.000001 or rect['y']+rect['height']>1.000001:
                        raise ValueError('Resaltado de PDF inválido.')
        normalized={k:note.get(k) for k in ('title','folder','content','shared','documentId','page')} | {'anchors':anchors,'writingScope':writing_scope,'pageNotes':page_notes}
        if 'contentFormat' in note:
            if note['contentFormat'] not in ('body','markdown'): raise ValueError('Formato de apunte inválido.')
            normalized['contentFormat']=note['contentFormat']
        return normalized

    def save_note(self, body):
        note=self.validate_note(body)
        note_id=body.get('id') or str(uuid.uuid4())
        if not isinstance(note_id,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',note_id): raise ValueError('ID de nota inválido.')
        with self.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row=conn.execute('SELECT body FROM notes WHERE id=?',(note_id,)).fetchone()
            old=json.loads(row['body']) if row else None
            if old and old.get('deletedAt'):
                raise ValueError('El apunte fue eliminado. El borrador local está conservado; copiá su texto en un apunte nuevo.')
            if old and body.get('revision')!=old['revision']:
                raise ValueError('La nota cambió en otra ventana. El borrador local está conservado; recargá antes de guardarlo.')
            if old and all(old.get(k)==v for k,v in note.items()):
                self._write_note_markdown(old,conn)
                return old
            if old:
                conn.execute('INSERT OR IGNORE INTO note_versions VALUES(?,?,?)',(note_id,old['revision'],row['body']))
            note.update({'id':note_id,'createdAt':old['createdAt'] if old else timestamp(),'updatedAt':timestamp(),'revision':old['revision']+1 if old else 1})
            conn.execute('INSERT OR REPLACE INTO notes VALUES(?,?)',(note_id,json.dumps(note,ensure_ascii=False)))
            self._write_note_markdown(note,conn)
        return note

    def delete_note(self, body):
        note_id=body.get('id')
        if not isinstance(note_id,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',note_id):
            raise ValueError('ID de nota inválido.')
        with self.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row=conn.execute('SELECT body FROM notes WHERE id=?',(note_id,)).fetchone()
            if not row: raise ValueError('Apunte inexistente.')
            note=json.loads(row['body'])
            if not note.get('deletedAt'):
                if type(body.get('revision')) is not int or body['revision']!=note['revision']:
                    raise ValueError('La nota cambió en otra ventana. Recargá antes de eliminarla.')
                # Preserve IDs, versions and tutor evidence; a stale autosave must
                # never bring a deleted note back into the active list.
                conn.execute('INSERT OR IGNORE INTO note_versions VALUES(?,?,?)',(note_id,note['revision'],row['body']))
                note={**note,'deletedAt':timestamp(),'revision':note['revision']+1}
                conn.execute('UPDATE notes SET body=? WHERE id=?',(json.dumps(note,ensure_ascii=False),note_id))
            (self.data/'notes'/(note_id+'.md')).unlink(missing_ok=True)
        return {'id':note_id,'deletedAt':note['deletedAt']}

    def _write_note_markdown(self, note, conn):
        # SQLite owns revisions; this private file is a readable mirror, written
        # under the same writer lock so an older save cannot replace a newer one.
        directory=self.data/'notes';directory.mkdir(mode=0o700,parents=True,exist_ok=True)
        documents=[json.loads(r['body']) for r in conn.execute('SELECT body FROM documents')]
        path=directory/(note['id']+'.md');temporary=directory/(note['id']+'.tmp')
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as stream:stream.write(note_markdown(note,documents))
            os.replace(temporary,path)
        finally:temporary.unlink(missing_ok=True)

    def save_draft(self, course, rationale, validate):
        validate(course)
        from assessment_rules import audit
        findings=audit(course)['findings']
        if findings:
            raise ValueError('Revisá las preguntas antes de guardar: '+json.dumps(findings,ensure_ascii=False))
        if not isinstance(rationale,str) or not rationale.strip() or len(rationale)>20000:
            raise ValueError('Explicá las fuentes, notas y criterios que motivan este curso.')
        draft={'id':str(uuid.uuid4()),'createdAt':timestamp(),'course':course,'rationale':rationale,'status':'draft'}
        with self.connect() as conn:
            conn.execute('INSERT INTO course_drafts VALUES(?,?)',(draft['id'],json.dumps(draft,ensure_ascii=False)))
        return {'id':draft['id'],'title':course['title'],'status':'draft','message':'Disponible para revisar e importar en Notas → Cursos preparados.'}

    def draft(self, draft_id):
        with self.connect() as conn:
            row=conn.execute('SELECT body FROM course_drafts WHERE id=?',(draft_id,)).fetchone()
        if not row: raise ValueError('Borrador inexistente.')
        return json.loads(row['body'])

    def author_context(self, folder=''):
        data=self.snapshot()
        notes=[n for n in data['notes'] if n['shared'] and (not folder or n['folder']==folder)]
        ids={n['id'] for n in notes}
        return {'notes':notes,'noteTutor':[q for q in data['noteTutor'] if q['noteId'] in ids], 'documents':data['documents'],'scope':'Solo notas actuales compartidas y sus consultas al tutor. Las notas privadas y sus versiones no se incluyen. Las respuestas del tutor son ayudas, nunca evidencia de dominio independiente. Los PDFs se consultan por páginas o leyendo su archivo local. No hay llamadas a modelos.'}

    def validate_backup(self, data):
        if not isinstance(data,dict): raise ValueError('Biblioteca del respaldo inválida.')
        for key in ('documents','notes','deletedNotes','noteVersions','courseDrafts','noteTutor','tutorContexts'):
            if not isinstance(data.get(key,[]),list): raise ValueError('Biblioteca del respaldo inválida.')
        docs={d['id']:d for d in self.snapshot()['documents']}
        for d in data.get('documents',[]):
            if not isinstance(d,dict) or not isinstance(d.get('id'),str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',d['id']) or not isinstance(d.get('title'),str) or not isinstance(d.get('sha256'),str) or not re.fullmatch(r'[0-9a-f]{64}',d['sha256']) or d.get('storage') not in ('source','upload'):
                raise ValueError('Documento del respaldo inválido.')
            self.document_path(d)
            if d['id'] in docs and docs[d['id']]['sha256']!=d['sha256']: raise ValueError('Documento local distinto del respaldo.')
            docs[d['id']]=d
        for n in data.get('notes',[])+data.get('deletedNotes',[])+data.get('noteVersions',[]):
            self.validate_note(n,docs)
            if not isinstance(n.get('id'),str) or type(n.get('revision')) is not int or n['revision']<1: raise ValueError('Versión de nota inválida.')
        local=self.snapshot()
        notes={n['id'] for n in local['notes']+local['deletedNotes']+data.get('notes',[])+data.get('deletedNotes',[])}
        for q in data.get('noteTutor',[]):
            if not isinstance(q,dict) or not isinstance(q.get('id'),str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',q['id']) or q.get('noteId') not in notes or q.get('status') not in ('pending','answered','failed') or q.get('helpProvided') is not True:
                raise ValueError('Consulta al tutor del respaldo inválida.')
            for k,limit in [('message',20000),('reply',100000),('error',2000),('createdAt',100)]:
                if not isinstance(q.get(k,''),str) or len(q.get(k,''))>limit: raise ValueError('Texto de consulta inválido.')
            context=q.get('context')
            if not isinstance(context,dict) or context.get('scope') not in ('page','general') or type(context.get('noteRevision')) is not int or context['noteRevision']<1:
                raise ValueError('Contexto de consulta inválido.')
            if context.get('documentId') is not None:
                doc=docs.get(context['documentId'])
                if not doc or context.get('sha256')!=doc['sha256'] or type(context.get('page')) is not int or context['page']<1 or (doc.get('pages') and context['page']>doc['pages']): raise ValueError('Fuente de consulta inválida.')
            elif context.get('scope')=='page' or context.get('page') is not None: raise ValueError('Página de consulta inválida.')
        import tutor_context
        for record in data.get('tutorContexts',[]):
            if not isinstance(record,dict) or record.get('id')!=tutor_context.target_key(record.get('target')) or type(record.get('revision')) is not int or record['revision']<1:
                raise ValueError('Preferencia de contexto inválida.')
            tutor_context.validate(record.get('selection'))
        return data

    def restore(self, conn, data):
        def archive(note):
            existing=conn.execute('SELECT body FROM note_versions WHERE id=? AND revision=?',(note['id'],note['revision'])).fetchone()
            if existing and json.loads(existing['body'])!=note:
                raise ValueError('Una versión anterior local difiere de la misma revisión del respaldo.')
            conn.execute('INSERT OR IGNORE INTO note_versions VALUES(?,?,?)',(note['id'],note['revision'],json.dumps(note,ensure_ascii=False)))
        for key,table in [('documents','documents'),('notes','notes'),('courseDrafts','course_drafts')]:
            for item in data.get(key,[])+(data.get('deletedNotes',[]) if key=='notes' else []):
                row=conn.execute('SELECT body FROM '+table+' WHERE id=?',(item['id'],)).fetchone()
                if not row: conn.execute('INSERT INTO '+table+' VALUES(?,?)',(item['id'],json.dumps(item,ensure_ascii=False)))
                elif key=='notes' and json.loads(row['body'])!=item:
                    # Restore merges the archived revision, never overwrites newer local work.
                    existing=json.loads(row['body'])
                    if item['revision']==existing['revision']: raise ValueError('Una nota local difiere del respaldo con la misma revisión.')
                    archive(item)
        for n in data.get('noteVersions',[]):
            archive(n)
        for q in data.get('noteTutor',[]):
            row=conn.execute('SELECT body FROM note_tutor WHERE id=?',(q['id'],)).fetchone()
            if row and json.loads(row['body'])!=q: raise ValueError('Una consulta local al tutor difiere del respaldo.')
            conn.execute('INSERT OR IGNORE INTO note_tutor VALUES(?,?)',(q['id'],json.dumps(q,ensure_ascii=False)))
        for record in data.get('tutorContexts',[]):
            # A backup never silently replaces a newer local context selection.
            row=conn.execute('SELECT body FROM tutor_contexts WHERE id=?',(record['id'],)).fetchone()
            if row and json.loads(row['body'])['revision']==record['revision'] and json.loads(row['body'])!=record:
                raise ValueError('Una preferencia local de contexto difiere del respaldo con la misma revisión.')
            conn.execute('INSERT OR IGNORE INTO tutor_contexts VALUES(?,?)',(record['id'],json.dumps(record,ensure_ascii=False)))
