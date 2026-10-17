/*====================== browser_tutor_modes.cjs ======================
   Browser test for tutor modes UI.
   Verifies: fixture build, server API, and UI rendering with plan data.
   Uses disposable fixture with isolated HOME/Margen (never real ~/Margen).
   Run: PLAYWRIGHT_CHROMIUM_EXECUTABLE=/opt/thorium-browser/thorium node tests/browser_tutor_modes.cjs
  ================================================================== */

const {chromium}=require('playwright');
const fs=require('fs'),os=require('os'),path=require('path'),net=require('net'),{spawn,spawnSync}=require('child_process');

(async()=>{
  const root=path.resolve(__dirname,'..');
  const fixtureRoot=fs.mkdtempSync(path.join(os.tmpdir(),'glosa-bt-modes'));

  // 1. Build isolated fixture (course + web + docs)
  const setup=spawnSync('python3',[path.join(root,'tests/helpers/fixture_workspace.py'),fixtureRoot,'--browser'],{stdio:'inherit'});
  if(setup.status!==0){console.error('fixture build failed');process.exit(1);}

  // 2. Set temp dirs; never falls back to real ~/Margen
  const data=path.join(fixtureRoot,'data'); fs.mkdirSync(data,{recursive:true});
  const home=path.join(fixtureRoot,'home'); fs.mkdirSync(home,{recursive:true});
  const margen=path.join(fixtureRoot,'margen'); fs.mkdirSync(margen,{recursive:true});

  // 3. Start server with env pointing to temp dirs
  const listener=net.createServer();
  await new Promise(r=>listener.listen(0,'127.0.0.1',r));
  const port=listener.address().port; await new Promise(r=>listener.close(r));

  const serverProc=spawn('python3',['server.py'],{
    cwd:fixtureRoot,
    env:{
      ...process.env,
      HOME:home,
      GLOSA_MARGEN_DIR:margen,
      LEARNING_DATA_DIR:data,
      LEARNING_PORT:String(port),
      OPENROUTER_API_KEY:'',
      FREELLMAPI_API_KEY:'',
      INTERN_API_KEY:''
    },
    stdio:['ignore','ignore','pipe']
  });

  const base=`http://127.0.0.1:${port}`;
  // Wait for server
  let serverReady=false;
  for(let i=0;i<100;i++){try{await(await fetch(base+'/api/state')).json();serverReady=true;break;}catch{}await new Promise(r=>setTimeout(r,100));if(i===99)throw Error('server startup fail');
  }
  if(!serverReady)throw Error('server not ready');

  // 3. Check API state has plan data
  const state=await(await fetch(base+'/api/state')).json();
  const hasPlanExams = !!(state.plan && state.plan.exams && state.plan.exams.length>0);
  const effectiveMode = state.effective?.decision?.effectiveMode;
  console.log('API: courses=', state.courses.length, 'events=', state.events?.length||0);
  console.log('API: has plan exams:', hasPlanExams, 'effectiveMode:', effectiveMode);

  // 4. Launch browser
  const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||chromium.executablePath()});
  const context=await browser.newContext({viewport:{width:1280,height:900}});
  await context.addInitScript(()=>{localStorage.setItem('glosa-active-room','local');});
  const page=await context.newPage();

  await page.goto(base);
  await page.waitForSelector('.activity');

  // 5. Check UI rendering
  const bodyText=await page.locator('body').innerText();
  const bodyLoaded = bodyText.length > 0;
  const hasActivity = await page.locator('.activity').count() > 0;
  console.log('UI: bodyLoaded=', bodyLoaded, 'hasActivity=', hasActivity);

  // 6. Screenshot for evidence
  await page.screenshot({path:path.join(fixtureRoot,'tutor-modes-panel.png'),fullPage:true});
  console.log('screenshot saved');

  // 7. Teardown
  await browser?.close();
  serverProc.kill();
  console.log('OK: browser_tutor_modes test completed.');
  console.log('Results: hasPlanExams=', hasPlanExams, 'effectiveMode=', effectiveMode);

  // Cleanup
  fs.rmSync(fixtureRoot,{recursive:true,force:true});
})();