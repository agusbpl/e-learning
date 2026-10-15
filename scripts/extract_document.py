"""Page-level text extraction for a user-supplied PDF; no model/network calls."""
import json
from pathlib import Path
import sys
from pypdf import PdfReader

if __name__=='__main__':
    source,target=map(Path,sys.argv[1:3])
    reader=PdfReader(source)
    if reader.is_encrypted and not reader.decrypt(''):
        raise SystemExit('El PDF requiere contraseña.')
    pages=[{'page':i+1,'text':page.extract_text() or ''} for i,page in enumerate(reader.pages)]
    target.write_text(json.dumps({'pages':pages},ensure_ascii=False))
