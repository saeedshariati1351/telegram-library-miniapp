"""Gallica: آزمون دوبارهٔ SRU با پرس‌وجوی ساده و ثبت پاسخ"""
import re, time, os
from hcommon import S, writer, log, OUT
w = writer('gallica.jsonl')
for lang in ('ara', 'per'):
    start, total = 1, None
    while True:
        q = f'dc.language all "{lang}" and dc.type all "monographie"'
        try:
            r = S.get('https://gallica.bnf.fr/SRU', params={'operation': 'searchRetrieve', 'version': '1.2', 'query': q, 'maximumRecords': 50, 'startRecord': start}, timeout=120)
        except Exception as e:
            log('gallica exc', e); break
        if not r.ok:
            log('gallica http', r.status_code, r.text[:300]); break
        x = r.text
        if total is None:
            m = re.search(r'numberOfRecords>(\d+)', x); total = int(m.group(1)) if m else 0; log('gallica', lang, total)
        recs = re.findall(r'(?s)<srw:record>(.*?)</srw:record>', x)
        if not recs: break
        for rec in recs:
            d = {}
            for k, v in re.findall(r'(?s)<dc:(\w+)[^>]*>(.*?)</dc:\1>', rec): d.setdefault(k, []).append(re.sub(r'\s+', ' ', v).strip())
            d['lang'] = lang; w(d)
        start += len(recs)
        if start > total or start > 30000: break
        time.sleep(1.5)
