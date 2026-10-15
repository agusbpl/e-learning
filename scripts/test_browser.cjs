// Run each browser scenario in its own process and report every failure.
const {readdirSync, mkdtempSync, rmSync} = require('node:fs');
const {join, resolve} = require('node:path');
const {spawnSync} = require('node:child_process');
const {tmpdir} = require('node:os');

const root = resolve(__dirname, '..');
const requested = process.argv.slice(2);
const files = readdirSync(join(root, 'tests'))
  .filter(name => /^browser_.*\.cjs$/.test(name) && (!requested.length || requested.includes(name))).sort();
if (requested.some(name => !files.includes(name))) {
  console.error('Unknown browser scenario'); process.exit(1);
}
const fixtureRoot = mkdtempSync(join(tmpdir(), 'glosa-browser-fixture-'));
try {
const setup = spawnSync('python3', [join(root, 'tests/helpers/fixture_workspace.py'), fixtureRoot, '--browser'], {stdio: 'inherit'});
if (setup.error || setup.status !== 0) process.exit(setup.status || 1);
const failed = [];
for (const name of files) {
  process.stdout.write(`\n=== ${name} ===\n`);
  const result = spawnSync(process.execPath, [join(fixtureRoot, 'tests', name)], {
    cwd: fixtureRoot,
    env: {
      ...process.env,
      OPENROUTER_API_KEY: '',
      FREELLMAPI_API_KEY: '',
      INTERN_API_KEY: '',
      GLOSA_MARGEN_DIR: '',
    },
    stdio: 'inherit',
    timeout: 180000,
  });
  if (result.error) console.error(result.error);
  if (result.status !== 0 || result.error) failed.push(name);
}
if (failed.length) {
  console.error(`\nFailed ${failed.length}/${files.length}: ${failed.join(', ')}`);
  process.exitCode = 1;
} else console.log(`\nOK: ${files.length} browser scenarios`);
} finally {
  rmSync(fixtureRoot, {recursive: true, force: true});
}
