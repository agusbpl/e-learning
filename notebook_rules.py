"""Select short, attributable notebook entries without replacing raw evidence."""
import re


def important_notes(proposals, message, previous, version):
    if not isinstance(proposals, list):
        return []
    seen = {re.sub(r'\s+', ' ', e['data'].get('text', '')).strip().casefold()
            for e in previous if e['kind'] == 'tutor_note' and e['data'].get('courseVersion') == version}
    notes = []
    for item in proposals[:3]:
        if not isinstance(item, dict) or item.get('kind') not in ('doubt', 'insight', 'decision'):
            continue
        text, quote = item.get('text'), item.get('quote')
        if not isinstance(text, str) or not 12 <= len(text.strip()) <= 600:
            continue
        if not isinstance(quote, str) or not 8 <= len(quote.strip()) <= 300 or quote.strip() not in message:
            continue
        key = re.sub(r'\s+', ' ', text).strip().casefold()
        if key in seen:
            continue
        seen.add(key)
        notes.append({'kind': item['kind'], 'text': text.strip(), 'quote': quote.strip(),
                      'courseVersion': version, 'author': 'tutor', 'isLearningEvidence': False})
    return notes
