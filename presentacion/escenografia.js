/* Dirección visual: composiciones distintas y una única mascota con tres modos. */
const mascotAsset='ilustraciones/glosa-tutora.png';
const mascot=(id,x,y,w,h,index=0)=>`<svg id="${id}" x="${x}" y="${y}" width="${w}" height="${h}" viewBox="${index*661} 0 661 793" preserveAspectRatio="xMidYMid meet" overflow="hidden"><defs><clipPath id="${id}-clip"><rect id="${id}-cliprect" x="${index*661}" y="0" width="661" height="793"/></clipPath></defs><image href="${mascotAsset}" width="1983" height="793" clip-path="url(#${id}-clip)"/></svg>`;
let mascotChoice=0;
const tutorVoices=[
 {name:'Flexible',color:'#e6ca73',eyebrow:'UNA LINTERNA PARA SEGUIR',words:['Vamos por una idea a la vez.','¿Qué entendiste del fragmento?','Lo pendiente sigue a la vista.'],detail:'Comprobación breve, sin borrar lo que falta trabajar.'},
 {name:'Estricta',color:'#9aaa85',eyebrow:'UNA LUPA SOBRE TU EXPLICACIÓN',words:['Miremos esa relación de cerca.','¿Cómo conectás estas dos ideas?','Mostrame dónde se sostiene.'],detail:'Comprensión con evidencia para cada criterio.'},
 {name:'Extrema',color:'#d88a52',eyebrow:'UN DESAFÍO EN TERRENO NUEVO',words:['Bien. Ahora cambiemos el caso.','¿Tu explicación sigue funcionando?','Probala frente a una objeción.'],detail:'Transferencia a otro caso; exigente y respetuosa.'}
];
scenes[5].title='Conocé a <em>Glosa.</em><br>Tu tutora de papel.';
scenes[5].intro='La misma compañera, tres modos.<br>Tocá una versión y descubrí su propuesta.';
scenes[5].note='Mascota ilustrativa · tutor opcional en Glosa o en tu agente externo · la ayuda no acredita dominio';
scenes[5].steps=[
 ['Flexible: una idea a la vez.','Una comprobación breve para seguir, conservando pendientes. En Glosa o con tu agente externo, elegís el contexto que compartís.','Mirar con lupa'],
 ['Estricta: sostené tu explicación.','Busca comprensión con evidencia por criterio. La conversación y las ayudas quedan registradas en el pliego.','Aceptar un desafío'],
 ['Extrema: probalo en otro caso.','Pide transferencia y defensa ante objeciones. Podés elegir el modo o activar Auto, que explica sus decisiones.','Organizar los parciales']
];
scenes[5].art=()=>svg('Glosa, mascota de papel: Flexible, Estricta y Extrema',`
<defs><radialGradient id="lantern-glow"><stop stop-color="#f1d274" stop-opacity=".65"/><stop offset="1" stop-color="#f1d274" stop-opacity="0"/></radialGradient></defs>
<g id="mascot-decor-0"><ellipse cx="278" cy="251" rx="260" ry="222" fill="url(#lantern-glow)"/><path d="M50 220q80-200 280-163" stroke="#c4b575" stroke-width="1" stroke-dasharray="3 8" fill="none"/><text x="65" y="110" class="scene-number" transform="rotate(-14 65 110)">una idea…</text></g>
<g id="mascot-decor-1"><circle cx="270" cy="238" r="199" stroke="#b6c1a5" fill="none" stroke-dasharray="2 12"/><path d="M80 180h35m-17-17v34M440 80h25m-13-13v26" stroke="#9eac8c"/><text x="65" y="120" class="scene-number">¿por qué?</text></g>
<g id="mascot-decor-2"><path d="M10 405 160 210 245 315 355 130 520 405" fill="#e7cdb1" opacity=".35"/><path d="M50 390Q150 320 180 345T325 200 405 80" fill="none" stroke="#ca895c" stroke-dasharray="4 9" stroke-width="2"/><text x="30" y="140" class="scene-number" transform="rotate(-12 30 140)">¿y si…?</text></g>
<g id="mascot-actor">${mascot('mascot-window',85,-15,420,430)}</g>
<g id="voice"><path d="M585 64h565q20 0 20 20v238q0 20-20 20H650l-62 40 18-40h-21q-20 0-20-20V84q0-20 20-20Z" fill="#fffdf5" filter="url(#shadow)"/>
${text(600,109,'UNA LINTERNA PARA SEGUIR','scene-label','id="voice-eyebrow"')}
${lines(600,171,tutorVoices[0].words,'scene-body',44).replaceAll('class="scene-body"','class="scene-body voice-line"')}
${text(600,312,tutorVoices[0].detail,'scene-small','id="voice-detail"')}
</g>
${[0,1,2].map(i=>button('mode-'+i,rect(105+i*365,428,340,69,i===0?'#e7d79f':'#eeeee2',`class="mode-background interactive-bg"`)+mascot('mini-'+i,112+i*365,401,88,95,i)+text(205+i*365,458,tutorVoices[i].name,'scene-body')+text(205+i*365,480,['Avanzar con una luz','Examinar la relación','Explorar un caso nuevo'][i],'scene-small'),'Elegir Glosa '+tutorVoices[i].name)).join('')}
`);
function chooseMascot(index,animate=true){mascotChoice=index;const d=tutorVoices[index];if(!$('#mascot-window'))return;const apply=()=>{$('#mascot-window').setAttribute('viewBox',`${index*661} 0 661 793`);$('#mascot-window-cliprect').setAttribute('x',String(index*661));$('#voice-eyebrow').textContent=d.eyebrow;$$('.voice-line').forEach((el,i)=>el.textContent=d.words[i]);$('#voice-detail').textContent=d.detail;[0,1,2].forEach(i=>{gsap.set('#mascot-decor-'+i,{autoAlpha:i===index?1:0});$('#mode-'+i).setAttribute('aria-pressed',String(i===index));gsap.set('#mode-'+i+' .mode-background',{fill:i===index?d.color:'#eeeee2'})});$('#status').textContent=`Glosa ${d.name}. ${d.words.join(' ')} ${d.detail}`;};gsap.killTweensOf('#mascot-actor,#voice');if(reduced||!animate){apply();gsap.set('#mascot-actor,#voice',{opacity:1,x:0,y:0,scale:1});return}gsap.to('#mascot-actor',{opacity:0,y:12,scale:.96,duration:.16,transformOrigin:'50% 80%',onComplete:()=>{apply();gsap.fromTo('#mascot-actor',{opacity:0,y:25,rotation:index===2?-7:2,scale:.92},{opacity:1,y:0,rotation:0,scale:1,duration:.7,ease:index===2?'back.out(1.7)':'power3.out'});gsap.fromTo('#voice',{opacity:.3,x:18},{opacity:1,x:0,duration:.5,ease:'power3.out'})}})}
scenes[5].build=()=>{gsap.set('#mascot-decor-1,#mascot-decor-2',{autoAlpha:0});const t=gsap.timeline({paused:true});t.to({progress:0},{progress:1,duration:4.6});return {t,times:[0,2.2,4.6]}};
scenes[5].interact=()=>{[0,1,2].forEach(i=>bind('#mode-'+i,()=>go(i)));$('#stage').addEventListener('pointermove',mascotParallax)};
scenes[5].onStep=i=>chooseMascot(i);
function mascotParallax(e){if(chapter!==5||reduced)return;const b=$('#stage').getBoundingClientRect();gsap.to('#mascot-actor',{x:(e.clientX-b.left-b.width/2)*.012,duration:.65,ease:'power2.out'})}
// Las conexiones se dibujan y los conceptos se pueden explorar.
scenes[3].title='Las ideas no viven <em>en casilleros.</em>';
scenes[3].intro='Seguí una conexión.<br>Descubrí otra forma de mirar el mismo concepto.';
scenes[3].art=()=>svg('Constelación de conceptos conectados',`
<g id="star-trails" stroke="#829a76" fill="none" stroke-width="1.5"><path d="M590 260 240 110"/><path d="M590 260 160 400"/><path d="M590 260 980 100"/><path d="M590 260 1040 410"/></g>
<g id="constellation-center"><circle cx="590" cy="260" r="104" fill="#e7d79f"/><circle cx="590" cy="260" r="121" fill="none" stroke="#a1af8d" stroke-dasharray="3 10"/>${text(590,255,'Modelo','scene-title','id="central-concept" text-anchor="middle"')}${text(590,286,'UNA IDEA, VARIOS CAMINOS','scene-label','text-anchor="middle" style="font-size:9px"')}</g>
<g id="satellites">${[[240,110,'Representación'],[160,400,'Abstracción'],[980,100,'Clase de teoría'],[1040,410,'Actividad']].map(([x,y,n],i)=>button('star-'+i,`<circle cx="${x}" cy="${y}" r="13" fill="#d5c587"/><circle cx="${x}" cy="${y}" r="25" fill="none" stroke="#82976d"/>`+text(x,y+58,n,'scene-body','text-anchor="middle"')+text(x,y+81,['Apunte relacionado','Referencia inversa','Mención en el material','Mención en un ejercicio'][i],'scene-small','text-anchor="middle"'),'Explorar '+n)).join('')}</g>
<g id="concept-card">${card(770,55,425,420,text(807,100,'FICHA DE CONCEPTO','scene-label')+text(807,148,'Modelo','scene-title')+rule(807,174,350)+lines(807,216,['Mi definición','Un ejemplo','Un contraejemplo','La fuente','Una pregunta para pensar'],'scene-body',45),'#edf0df')}</g>
`);
scenes[3].build=()=>{const t=timeline(['#satellites','#concept-card']);$$('#star-trails path').forEach(p=>{const n=p.getTotalLength();gsap.set(p,{strokeDasharray:n,strokeDashoffset:n});t.to(p,{strokeDashoffset:0,duration:1.2,ease:'power2.inOut'},.3)});reveal(t,'#satellites',.7,{scale:.9,transformOrigin:'50% 50%'});t.to('#satellites,#star-trails',{autoAlpha:0,duration:.6},2.8);t.to('#constellation-center',{x:-230,duration:1,ease:'power3.inOut'},2.9);reveal(t,'#concept-card',3,{x:70,rotation:4});return {t,times:[0,2.4,4.8]}};
scenes[3].interact=()=>['Representación','Abstracción','Clase de teoría','Actividad'].forEach((n,i)=>bind('#star-'+i,()=>{stopAuto();$('#central-concept').textContent=n;$('#central-concept').style.fontSize=n.length>12?'23px':'30px';if(!reduced)gsap.fromTo('#constellation-center',{scale:.93,transformOrigin:'50% 50%'},{scale:1,duration:.6,ease:'back.out(1.8)'});$('#status').textContent='Concepto seleccionado: '+n+'. Podés recorrer referencias y menciones.'}));
scenes[4].title='Acá hubo un error.<br><em>Acá puede empezar algo.</em>';
const errorArt=scenes[4].art;
scenes[4].art=()=>errorArt().replace('</svg>',`<g id="aha"><circle cx="1030" cy="95" r="64" fill="#d79765"/>${text(1030,109,'¡Ajá!','scene-title','text-anchor="middle" transform="rotate(12 1030 109)"')}</g><path id="pencil-line" d="M185 286q120-14 325 1" stroke="#c3744b" stroke-width="3" fill="none"/></svg>`);
const errorBuild=scenes[4].build;
scenes[4].build=()=>{const result=errorBuild();gsap.set('#aha',{autoAlpha:0,scale:.3,transformOrigin:'50% 50%'});const p=$('#pencil-line'),n=p.getTotalLength();gsap.set(p,{strokeDasharray:n,strokeDashoffset:n});result.t.to(p,{strokeDashoffset:0,duration:.65,ease:'power2.out'},.25);result.t.to('#aha',{autoAlpha:1,scale:1,rotation:-8,duration:.7,ease:'back.out(2)'},3.3);return result};
scenes[7].title='No empezás de cero. <em>Retomás el hilo.</em>';
scenes[7].art=()=>svg('Continuidad del recorrido de estudio',group('markdown',iconDoc(260,140)+text(335,170,'Una idea.md','scene-title')+text(335,213,'Tu archivo. Tus palabras.','scene-body')+lines(335,270,['Editable con otro editor.','Revisiones y conflictos a la vista.'],'scene-detail',32))+group('backup-link','<path d="M630 230q150-140 290 0" fill="none" stroke="#b59b57" stroke-width="2" stroke-dasharray="4 8"/><circle id="backup-dot" cx="630" cy="230" r="6" fill="#b59b57"/>')+group('backup',folder(850,165,250,180)+text(880,232,'RESPALDO','scene-label')+text(880,281,'Tu recorrido.','scene-body'))+group('closing',`<path id="closing-thread" d="M100 280C230 65 360 490 505 265S780 70 920 280 1150 420 1190 180" fill="none" stroke="#b1a06c" stroke-width="2"/>${[[170,210,'Preparar'],[390,330,'Leer'],[620,160,'Conectar'],[870,210,'Practicar'],[1080,340,'Retomar']].map(([x,y,n],i)=>group('journey-'+i,`<circle cx="${x}" cy="${y}" r="40" fill="${['#c5d1b5','#e8d998','#a9bc98','#e0b18c','#c5d1b5'][i]}"/>`+text(x,y+8,String(i+1).padStart(2,'0'),'scene-number','text-anchor="middle"')+text(x,y+78,n,'scene-body','text-anchor="middle"'))).join('')}`));
scenes[7].build=()=>{const t=timeline(['#backup','#backup-link','#closing']);reveal(t,'#backup-link',.2);reveal(t,'#backup',.7,{y:-40,rotation:7});t.to('#backup-dot',{attr:{cx:850,cy:230},duration:1.2},.4);t.to('#markdown,#backup,#backup-link',{autoAlpha:0,duration:.5},2.6);reveal(t,'#closing',2.8);const p=$('#closing-thread'),n=p.getTotalLength();gsap.set(p,{strokeDasharray:n,strokeDashoffset:n});t.to(p,{strokeDashoffset:0,duration:1.8,ease:'power2.inOut'},2.9);for(let i=0;i<5;i++){gsap.set('#journey-'+i,{autoAlpha:0});reveal(t,'#journey-'+i,3+i*.23,{y:20,scale:.8,transformOrigin:'50% 50%'})}return {t,times:[0,2.3,5.2]}};
// Composición y entradas específicas por escena.
const originalOpenChapter=openChapter;
openChapter=function(n,toStep=0,manual=true){document.body.dataset.scene=String(Math.max(0,Math.min(7,n)));originalOpenChapter(n,toStep,manual);if(!reduced){enterTween?.kill();gsap.set('#stage',{opacity:1,x:0,y:0,scale:1});const entrances=[{x:70,rotation:1.5},{x:-60,rotation:-2},{y:25},{scale:.95},{y:45,rotation:2},{y:25},{x:30},{scale:1.04}];enterTween=gsap.from('#stage',{...entrances[chapter],opacity:0,duration:.85,ease:'power3.out'});gsap.fromTo('#title',{opacity:0,y:18},{opacity:1,y:0,duration:.7,ease:'power3.out'})}};
const originalUpdate=update;
update=function(){originalUpdate();scenes[chapter].onStep?.(step);document.body.dataset.step=String(step)};
fromHash();
const originalMotionUI=motionUI;
motionUI=function(){originalMotionUI();document.body.dataset.motion=reduced?'reduced':'full'};
motionUI();
