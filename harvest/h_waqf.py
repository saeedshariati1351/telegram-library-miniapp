"""المكتبة الوقفية: همهٔ صفحه‌های فهرست (initialBooks در داده‌های Next.js)"""
import re, json
from hcommon import get, writer, log, pmap
w = writer('waqfeya.jsonl')
def page(p):
    r = get(f'https://waqfeya.net/books?page={p}')
    if not r: return 0
    u = ''.join(json.loads('"' + m + '"') for m in re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', r.text))
    i = u.find('"initialBooks":')
    if i < 0: return 0
    j = u.find('[', i); d = 0
    for k in range(j, len(u)):
        if u[k] == '[': d += 1
        elif u[k] == ']':
            d -= 1
            if d == 0: break
    arr = json.loads(u[j:k + 1])
    for b in arr: w(b)
    return len(arr)
n = pmap(page, range(1, 400), 4)
log('waqfeya', sum(n))
