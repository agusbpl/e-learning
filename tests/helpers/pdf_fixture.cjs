function fixturePDF(){
  const stream=n=>`BT /F1 18 Tf 40 700 Td (PDF temporal pagina ${n}) Tj ET`;
  const objects=['<< /Type /Catalog /Pages 2 0 R >>','<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>',...[5,6].map(n=>`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 7 0 R >> >> /Contents ${n} 0 R >>`),...[1,2].map(n=>`<< /Length ${stream(n).length} >>\nstream\n${stream(n)}\nendstream`),'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'];
  let pdf='%PDF-1.4\n',offsets=[0];objects.forEach((body,i)=>{offsets.push(Buffer.byteLength(pdf));pdf+=`${i+1} 0 obj\n${body}\nendobj\n`;});const at=Buffer.byteLength(pdf);pdf+=`xref\n0 ${offsets.length}\n0000000000 65535 f \n`+offsets.slice(1).map(n=>String(n).padStart(10,'0')+' 00000 n \n').join('')+`trailer\n<< /Size ${offsets.length} /Root 1 0 R >>\nstartxref\n${at}\n%%EOF\n`;return Buffer.from(pdf);
}
module.exports={fixturePDF};
