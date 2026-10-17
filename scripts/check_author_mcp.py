"""Real stdio integration check, using an isolated temporary study database."""
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
from mcp import Client, StdioServerParameters

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'tests/helpers'))
from fixture_workspace import build, fixture_course


def payload(result):
    assert not result.is_error, result
    if result.structured_content is not None:return result.structured_content
    return json.loads(result.content[0].text)


async def main():
    with tempfile.TemporaryDirectory(prefix='author-mcp-check-') as directory:
        fixture_root=build(Path(directory)/'fixture-root')
        data=Path(directory)/'data';data.mkdir()
        os.environ['LEARNING_DATA_DIR']=str(data)
        os.environ['OPENROUTER_API_KEY']=''
        import server
        server.ROOT=fixture_root
        server.init_db()
        library=server.library()
        note={'title':'Apunte de clase','folder':'Materia nueva','content':'DUDA COMPARTIDA PARA EL CURSO','shared':True,'documentId':None,'page':None,'anchors':[]}
        library.save_note(note)
        private=library.save_note({**note,'shared':False,'content':'NO EXPONER NOTA PRIVADA'})
        # Previous shared revisions must disappear from author context when made private.
        prior=library.save_note({**note,'content':'NO EXPONER VERSIÓN ANTERIOR'})
        library.save_note({**prior,'shared':False})
        course=fixture_course()
        course['id']='curso-integracion-mcp'
        current=server.snapshot()['courses'][0]
        server.event('annotation',current['id'],current['lessons'][0]['id'],{'comment':'NO EXPONER ANOTACIÓN PRIVADA','shareWithTutor':False})
        server.event('answer',current['id'],current['lessons'][0]['id'],{'text':'EVIDENCIA ORIGINAL'})
        parameters=StdioServerParameters(command=sys.executable,args=[str(fixture_root/'author_mcp.py')],env={**os.environ,'LEARNING_DATA_DIR':str(data),'OPENROUTER_API_KEY':''})
        async with Client(parameters) as client:
            tools=await client.list_tools()
            assert {'author_brief','read_document_pages','study_history','validate_course','save_course_draft'} <= {t.name for t in tools.tools}
            brief=payload(await client.call_tool('author_brief',{'folder':'Materia nueva'}))
            assert len(brief['notes'])==1
            assert 'NO EXPONER' not in json.dumps(brief)
            assert brief['existingCourse'] is None
            history=payload(await client.call_tool('study_history',{'course_id':current['id']}))
            assert 'EVIDENCIA ORIGINAL' in json.dumps(history)
            assert 'NO EXPONER' not in json.dumps(history)
            documents=await client.call_tool('list_documents',{})
            assert not documents.is_error
            doc=brief['documents'][0]
            pages=payload(await client.call_tool('read_document_pages',{'document_id':doc['id'],'start':1}))
            assert pages['pages'][0]['page']==1
            validated=payload(await client.call_tool('validate_course',{'course':course}))
            assert validated['valid']
            draft=payload(await client.call_tool('save_course_draft',{'course':course,'rationale':'Prueba de un nuevo curso generado a partir de apuntes.'}))
            assert draft['status']=='draft'
            invalid={**course,'schemaVersion':99}
            rejected=await client.call_tool('save_course_draft',{'course':invalid,'rationale':'No debe guardarse'})
            assert rejected.is_error
            assert 'schemaVersion' in rejected.content[0].text
            calendar_event=payload(await client.call_tool('save_calendar_event',{'event':{'courseId':current['id'],'title':'Clase de prueba MCP','kind':'theory','date':'2026-10-12','time':'18:00','repeatUntil':'2026-11-30'}}))
            calendar=payload(await client.call_tool('list_calendar_events',{'course_id':current['id']}))
            assert calendar['events']==[calendar_event]
            deleted=payload(await client.call_tool('delete_calendar_event',{'event_id':calendar_event['id'],'expected_revision':calendar_event['revision']}))
            assert deleted['deleted']
            baseline={**course,'id':'curso-loop-mcp'}
            with server.connect() as conn:conn.execute('INSERT INTO courses VALUES(?,?)',(baseline['id'],json.dumps(baseline,ensure_ascii=False)))
            request=server.event('continuation_requested',baseline['id'],baseline['lessons'][0]['id'],{'courseVersion':baseline['version'],'sourceEventIds':[]})
            requests=payload(await client.call_tool('pending_continuations',{'course_id':baseline['id']}))
            assert requests['requests'][0]['id']==request['id']
            handoff=payload(await client.call_tool('continuation_brief',{'request_id':request['id']}))
            assert handoff['existingCourse']['id']==baseline['id']
            assert 'NO EXPONER' not in json.dumps(handoff)
            updated={**baseline,'version':'loop-2'}
            args={'request_id':request['id'],'course':updated,'expected_version':baseline['version'],'rationale':'Continuación basada en evidencia compartida de esta prueba.'}
            applied=payload(await client.call_tool('apply_continuation',args))
            assert applied['applied'] and not applied['alreadyApplied']
            assert payload(await client.call_tool('apply_continuation',args))['alreadyApplied']
            # New default: source folder -> a complete directory, opened directly
            # from GLOSA, without a draft, ZIP or fictional student responses.
            source_brief=payload(await client.call_tool('source_folder_brief',{'folder':str(fixture_root/'sources')}))
            pdf=next(item for item in source_brief['files'] if item['path']=='fixture.pdf')
            ready_course=json.loads(json.dumps(course))
            ready_course['sources'][0]['url']='/documents/'+pdf['documentId']
            ready=payload(await client.call_tool('create_study_pliego',{
                'folder':str(fixture_root/'sources'),'title':'Autoría directa temporal',
                'course':ready_course,'rationale':'Prueba del contrato de entrega, no evaluación del alumno.',
                'study_plan':{'examDate':'2026-10-20'},
                'calendar_events':[{'title':'Parcial temporal','kind':'exam','date':'2026-10-20','time':'19:00'}]}))
            assert ready['status']=='ready' and (Path(ready['path'])/'pliego.json').is_file()
            direct=payload(await client.call_tool('author_brief',{'course_id':ready_course['id']}))
            assert direct['roomId']==ready['id'] and direct['existingCourse']==ready_course
            assert direct['courseCalendar'][0]['time']=='19:00'
            assert payload(await client.call_tool('study_history',{'course_id':ready_course['id']}))['events']==[]
            native=payload(await client.call_tool('save_native_note',{'note':{'title':'SI','folder':'Glosario','content':'# SI\n\nSistema de información.','contentFormat':'markdown','shared':True,'documentId':None,'page':None,'anchors':[]}}))
            assert native['url']=='#note='+native['note']['id']
            assert list((Path(ready['path'])/'Apuntes'/'Glosario').glob('SI.md'))
            lesson=ready_course['lessons'][0];block=lesson['blocks'][0]
            edit={'course_id':ready_course['id'],'lesson_id':lesson['id'],'block_id':block['id'],
                  'text':'[SI]('+native['url']+')','expected_version':ready_course['version'],
                  'new_version':'native-glossary-2','rationale':'Enlazar la nota nativa conservando la historia.'}
            assert payload(await client.call_tool('update_course_block',edit))['version']=='native-glossary-2'
            assert (await client.call_tool('update_course_block',edit)).is_error
            changed=payload(await client.call_tool('author_brief',{'course_id':ready_course['id']}))['existingCourse']
            assert changed['lessons'][0]['blocks'][0]['text']==edit['text']
            import sqlite3
            with sqlite3.connect(Path(ready['path'])/'learning'/'learning.sqlite3') as archived:
                versions=[json.loads(row[0]) for row in archived.execute("SELECT body FROM events WHERE kind='course_version'")]
            assert any(v['previousCourse']==ready_course for v in versions)
            second=changed['lessons'][0]['blocks'][1]
            batch={'course_id':ready_course['id'], 'expected_version':changed['version'],
                   'new_version':'native-inline-3', 'rationale':'Integrar enlaces y retirar bloque redundante.',
                   'changes':[{'lessonId':lesson['id'],'blockId':block['id'],'text':'Un [SI]('+native['url']+') integra datos.'},
                              {'lessonId':lesson['id'],'blockId':second['id'],'remove':True}]}
            assert payload(await client.call_tool('update_course_blocks',batch))['changedBlocks']==2
            inline=payload(await client.call_tool('author_brief',{'course_id':ready_course['id']}))['existingCourse']
            assert second['id'] not in {b['id'] for b in inline['lessons'][0]['blocks']}
            assert inline['lessons'][0]['exercises']==changed['lessons'][0]['exercises']
            assert inline['lessons'][1:]==changed['lessons'][1:]
            invalid_batch={**batch,'expected_version':inline['version'],'new_version':'invalid-4',
                           'changes':[batch['changes'][0],{'lessonId':lesson['id'],'blockId':'nonexistent','remove':True}]}
            assert (await client.call_tool('update_course_blocks',invalid_batch)).is_error
            assert payload(await client.call_tool('author_brief',{'course_id':ready_course['id']}))['existingCourse']==inline
        async with Client(parameters,mode='legacy') as client:
            brief=payload(await client.call_tool('author_brief',{'folder':'Materia nueva'}))
            assert len(brief['notes'])==1
        data=server.snapshot()
        assert course['id'] not in {c['id'] for c in data['courses']}
        assert len(data['library']['courseDrafts'])==1
        assert library.snapshot()['notes'][1]==private
    print('MCP stdio (actual y handshake legacy): consulta, privacidad, paginado, validación, compatibilidad legada y pliego completo directo OK. Base temporal eliminada.')


if __name__=='__main__':asyncio.run(main())
