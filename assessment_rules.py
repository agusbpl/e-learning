"""Deterministic item checks and evidence gates; not a semantic truth oracle."""
import re
import secrets
import statistics

def random_order(count):
    if type(count) is not int or not 2 <= count <= 200:
        raise ValueError('Se necesitan entre 2 y 200 elementos.')
    order = list(range(count))
    secrets.SystemRandom().shuffle(order)
    return order

def audit(course):
    findings = []
    for lesson in course['lessons']:
        for ex in lesson['exercises']:
            if ex['type'] != 'choice': continue
            opts = ex['options']
            normalized = [' '.join(s.lower().split()) for s in opts]
            issues = []
            if len(set(normalized)) != len(opts): issues.append('Hay opciones duplicadas.')
            lengths = [len(re.findall(r'\w+', s)) for s in opts]
            key = ex['correctIndex']
            others = [n for i,n in enumerate(lengths) if i != key]
            if lengths[key] > max(others) and lengths[key] >= statistics.median(others) * 1.5 and lengths[key] - min(others) >= 4:
                issues.append('La clave es la única opción larga: revisá la pista por longitud.')
            if any(re.search(r'\b(todas las anteriores|ninguna de las anteriores|opción [a-d]|opciones [a-d]|las dos anteriores)\b', s, re.I) for s in opts):
                issues.append('Hay referencias a posiciones; el orden aleatorio cambiaría el significado.')
            findings.extend({'lessonId':lesson['id'],'exerciseId':ex['id'],'issue':s} for s in issues)
    return {'findings':findings, 'semanticReviewRequired':True,
            'scope':'Detecta algunas pistas mecánicas; no prueba exactitud, plausibilidad ni ausencia de sesgos.'}

def evidence_gate(assessment, lesson, answers, message):
    checks = assessment.get('criterionChecks', [])
    choice_ids={ex['id'] for ex in lesson['exercises'] if ex['type']=='choice'}
    texts = [message] + [str(e['data'].get(k,'')) for e in answers if not e['data'].get('helpReceived',False) for k in ('text','reasoning') if not(k=='text' and e['data'].get('exerciseId') in choice_ids)]
    required = {(ex['id'], criterion) for ex in lesson['exercises'] for criterion in ex['rubric']}
    supported = set()
    if isinstance(checks,list):
        for c in checks:
            if not isinstance(c,dict): continue
            pair = (c.get('exerciseId'),c.get('criterion'))
            quote = c.get('quote')
            if pair in required and c.get('result')=='met' and c.get('independent') is True and isinstance(quote,str) and quote.strip() and any(quote in t for t in texts):
                supported.add(pair)
    if assessment['status']=='independent' and required - supported:
        assessment['status']='pending'
        assessment['reason']='Falta evidencia original verificable para todos los criterios. '+assessment.get('reason','')
    assessment['evaluationPolicyVersion']='2026-10-10.1'
    assessment['criterionChecks']=checks if isinstance(checks,list) else []
    return assessment
