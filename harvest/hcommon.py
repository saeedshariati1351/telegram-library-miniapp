import json, os, re, time, random, threading, requests
from concurrent.futures import ThreadPoolExecutor
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'out'))
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36 library-miniapp"}
S = requests.Session(); S.headers.update(UA)
_lock = threading.Lock()

def get(url, tries=4, timeout=60, **kw):
    for k in range(tries):
        try:
            r = S.get(url, timeout=timeout, **kw)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(str(r.status_code))
            return r
        except Exception as e:
            if k == tries - 1:
                log('ERR', url, e); return None
            time.sleep(2 ** k + random.random())

def log(*a):
    with _lock:
        with open(os.path.join(OUT, '_log.txt'), 'a', encoding='utf-8') as f:
            f.write(' '.join(str(x) for x in a) + '\n')

def writer(name):
    f = open(os.path.join(OUT, name), 'a', encoding='utf-8')
    def w(obj):
        with _lock:
            f.write(json.dumps(obj, ensure_ascii=False) + '\n'); f.flush()
    return w

def pmap(fn, items, workers=6):
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(fn, items))

def text(html):
    html = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', html)
    html = re.sub(r'(?s)<[^>]+>', ' ', html)
    import html as H
    return re.sub(r'\s+', ' ', H.unescape(html)).strip()
