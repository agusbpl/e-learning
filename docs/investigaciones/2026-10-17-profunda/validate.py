from pathlib import Path
import hashlib,json
base=Path('/tmp/glosa-deep-20261017');checks=[]
def check(name,ok,detail):
 assert ok,(name,detail)
 checks.append({'check':name,'passed':True,'detail':detail})
idx=json.load((base/'obsidian/corpus/INDEX.json').open());source=Path('/tmp/glosa-obsidian-research/evidence/obsidian_app.js').read_bytes()
check('Obsidian: source identity',hashlib.sha256(source).hexdigest()==idx['source_sha256'],idx['source_sha256'])
for row in idx['index']:
 a,b=row['ast_byte_range'];check('Obsidian fragment '+row['id'],hashlib.sha256(source[a:b]).hexdigest()==row['orig_slice_sha256'],row['name'])
check('Obsidian: 90 selected functions',len(idx['index'])==90,'Corpus reducido, no app completa')
d=json.load((base/'obsidian/evidence/re05-corpus-analysis.json').open());n=d['normalized_result'];check('Obsidian: REA parse',n['statistics']['parse_failures']==0 and n['statistics']['parsed_javascript_files']==90,d['evidence_id'])
for p in (base/'obsidian/evidence').glob('trace-*.json'):
 if 'input' in p.name:continue
 t=json.load(p.open());check('Obsidian trace '+p.name,'evidence_id' in t,{'id':t.get('evidence_id'),'terminal_paths':len(t.get('normalized_result',{}).get('paths',[]))})
prov=json.load((base/'okular/fragments/provenance.json').open());native=Path(prov['source']).read_bytes();derived=Path(prov['derived']).read_bytes()
check('Okular: original identity',hashlib.sha256(native).hexdigest()==prov['sourceSha256'],prov['sourceSha256'])
for row in prov['functions']:
 raw=native[row['sourceFileOffset']:row['sourceFileOffset']+row['byteLength']];frag=derived[row['derivedFileOffset']:row['derivedFileOffset']+row['byteLength']]
 check('Okular exact bytes '+row['name'],raw==frag and hashlib.sha256(raw).hexdigest()==row['sha256'],row['sourceVirtualAddress'])
for name in ('nextBookmark','previousBookmark','viewportLess','viewportToString','continueSearch','setViewportPage'):
 d=json.load((base/'okular/fragments'/ (name+'.json')).open());n=d['normalized_result'];check('Okular REA function '+name,d['operation']=='analyze_function' and bool(n['pseudocode']) and len(n['basic_blocks'])>0,d['evidence_id'])
ko=[]
for i in range(1,6):
 d=json.load((base/f'koreader/out/rea-s{i}.json').open());n=d['normalized_result'];s=''.join(f['data'] for f in n['frames']);ko.append(s)
 check('KOReader REA capture '+str(i),n['exit']['code']==0 and not n['truncated'] and 'MODULE_OK' in s,d['evidence_id'])
check('KOReader vocab observations',all(x in ko[0] for x in ('delta=1800','delta=300','delta=165888000')),'Primer acierto 30 min; olvido 5 min; techo de intervalo')
check('KOReader timer observations',all(x in ko[1] for x in ('REM_3661_raw H=1 M=1 S=1','REM_3661_rounddown H=1 M=0 S=0','REM_UNSCHEDULED=inf H=nil')),'Reloj stub explícito; descomposición real')
check('KOReader Markdown observations',all(x in ko[2] for x in ('**Concepto clave**','## Cap 2','pos=/body/xp1')),'Contenido y backlinks de datos de prueba')
check('KOReader history observations',all(x in ko[3] for x in ('ORDER=1:a.epub 2:c.epub 3:b.epub','D_SELECT_ENABLED=false','PREV_OF_A=/books/c.epub')),'Filesystem stub explícito')
check('KOReader context observations',all(x in ko[4] for x in ('mandatory=p42','<H>sin espacio <B>clave</B>. Fin','RESULT_COUNT=3')),'Documento y widgets stub explícito')
for app in ('obsidian','koreader'):
 j=json.load((base/app/'inventario.json').open());rs=j['funcionalidades'];check(app+' inventory',len(rs)==20 and len({r['id'] for r in rs})==20,'20 filas distintas, propuestas sujetas a revisión')
audit=json.load((base/'glosa-audit.json').open());check('Glosa audit',len(audit['entries'])==46,'Revisión estática fuente; no prueba de runtime')
(base/'validacion.json').write_text(json.dumps({'scope':'Comprobación mecánica de procedencia y resultados de herramientas; NO evaluación de aprendizaje ni validación semántica de todas las propuestas.','checks':checks},ensure_ascii=False,indent=2))
print('Passed',len(checks),'checks of evidence provenance/output. No student database used.')
