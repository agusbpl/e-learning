// Classic scrollbars must not make fit-to-width pages oscillate on opening.
const {chromium}=require('playwright');
const fs=require('fs'),os=require('os'),path=require('path'),http=require('http'),net=require('net'),assert=require('assert/strict'),{spawn}=require('child_process');
const get=url=>new Promise((resolve,reject)=>http.get(url,{headers:{Connection:'close'}},r=>{r.resume();r.on('end',()=>resolve(r.statusCode));}).on('error',reject));
(async()=>{
 const root=path.resolve(__dirname,'..'),data=fs.mkdtempSync(path.join(os.tmpdir(),'glosa-pdf-layout-')),listener=net.createServer();
 await new Promise(r=>listener.listen(0,'127.0.0.1',r));const port=listener.address().port;await new Promise(r=>listener.close(r));
 const service=spawn('python3',['-c',`import server
server.init_db()
doc=next(d for d in server.library().snapshot()['documents'] if d['pages']>=2)
server.library().save_note({'title':'PDF estable','folder':'','content':'','shared':False,'documentId':doc['id'],'page':1,'writingScope':'page','pageNotes':{doc['id']:{'1':'Conservar este texto'}},'anchors':[]})
server.ThreadingHTTPServer(('127.0.0.1',server.PORT),server.Handler).serve_forever()
`],{cwd:root,env:{...process.env,LEARNING_DATA_DIR:data,LEARNING_PORT:String(port)},stdio:'ignore'});
 let browser;
 try{
  const base=`http://127.0.0.1:${port}`;
  for(let i=0;i<100;i++){try{if(await get(base+'/api/state')===200)break;}catch{}await new Promise(r=>setTimeout(r,100));if(i===99)throw Error('Server unavailable');}
  // Playwright normally hides scrollbars in headless mode, masking this bug.
  browser=await chromium.launch({headless:true,ignoreDefaultArgs:['--hide-scrollbars'],executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||chromium.executablePath()});
  const page=await browser.newPage({viewport:{width:1100,height:933}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>localStorage.setItem('glosa-active-room','local'));
  await page.goto(base);await page.waitForSelector('.activity');
  // Exercise a 15px classic scrollbar regardless of the desktop theme.
  await page.addStyleTag({content:'#pdf-scroll::-webkit-scrollbar{width:15px;height:15px}'});
  await page.keyboard.type('gn');await page.evaluate(()=>ClassNotes.openList());
  await page.locator('.class-note-link').filter({hasText:'PDF estable'}).click();
  await page.waitForFunction(()=>document.querySelector('#pdf-page-canvas .textLayer')?.childElementCount>0&&document.getElementById('pdf-loading').hidden);
  const assertStable=async label=>{
  await page.waitForTimeout(650);
  const stable=await page.evaluate(async()=>{
   const scroll=document.getElementById('pdf-scroll'),canvas=document.querySelector('#pdf-page-canvas canvas'),samples=[];
   for(let i=0;i<12;i++){
    samples.push({reader:scroll.clientWidth,page:parseFloat(document.querySelector('#pdf-page-canvas canvas').style.width)});
    await new Promise(r=>setTimeout(r,100));
   }
   return {samples,sameCanvas:canvas.isConnected};
  });
  assert(stable.sameCanvas,label+': opening the PDF must settle instead of continuously replacing its canvas: '+JSON.stringify(stable.samples));
  assert(Math.max(...stable.samples.map(s=>s.reader))-Math.min(...stable.samples.map(s=>s.reader))<=1,'Reader width oscillates');
  assert(stable.samples.every(s=>Math.abs(s.page-(s.reader-40))<1),'The page must fit the final reader width');
  };
  await assertStable('Overflow threshold');
  // Actual eDP panel resolution, plus space occupied by browser chrome.
  for(const height of [768,650]){
   await page.setViewportSize({width:1366,height});await assertStable('eDP 1366x'+height);
  }
  assert.equal(await page.locator('#pdf-page').inputValue(),'1');
  assert.equal(await page.locator('.note-cell-content').first().inputValue(),'Conservar este texto');
  assert.deepEqual(errors,[]);
  console.log('OK: initial PDF layout settles with visible classic scrollbars near the vertical overflow threshold; page and notes preserved.');
 }finally{await browser?.close();service.kill();fs.rmSync(data,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exit(1);});
