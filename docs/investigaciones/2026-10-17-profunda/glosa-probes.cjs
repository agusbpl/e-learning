const fs=require('fs'),vm=require('vm');
const source=fs.readFileSync('<HOME>/Documents/glosa/web/app.js','utf8');
const fn=source.match(/function safeSourceUrl\(source,page\) \{[^\n]+\}/)[0];
const scope={GlosaRoom:{url:u=>u}};vm.createContext(scope);vm.runInContext(fn,scope);
const rows=['/sources/a.pdf','/documents/doc-1','https://example.org/a.pdf','javascript:alert(1)'].map(url=>({url,result:scope.safeSourceUrl({url},3)}));
fs.writeFileSync('/tmp/glosa-deep-20261017/glosa-source-links-probe.json',JSON.stringify({source:'web/app.js',function:'safeSourceUrl',scope:'Función real extraída del repo y ejecutada aislada en Node; sin datos personales ni servidor.',rows},null,2));
if(rows[1].result!==null)throw Error('Cambió el resultado; revisar el hallazgo');
console.log(JSON.stringify(rows));
