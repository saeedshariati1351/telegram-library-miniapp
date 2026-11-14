"""آزمون دسترسی پایگاه‌های ناآزموده از سرور GitHub"""
import os
from hcommon import get, log, OUT
os.makedirs(os.path.join(OUT, 'probe3'), exist_ok=True)
U = {'shiaonline_home': 'https://shiaonlinelibrary.com/', 'shiaonline_books': 'https://shiaonlinelibrary.com/الكتب',
     'thaq_home': 'https://thaqalaynlibrary.com/', 'thaq_books': 'https://thaqalaynlibrary.com/books', 'tebyan': 'https://library.tebyan.net/fa',
     'nlai': 'https://dl.nlai.ir/', 'ical': 'https://dlib.ical.ir/', 'ical2': 'https://ical.ir/', 'aqr': 'https://digital.aqr.ir/', 'ut': 'https://utdlib.ut.ac.ir/',
     'mostafa': 'https://pdf.al-mostafa.com/', 'mostafa2': 'http://www.al-mostafa.com/', 'alislam': 'https://www.al-islam.org/library', 'alislam_sitemap': 'https://www.al-islam.org/sitemap.xml',
     'ketabnak_books': 'https://www.ketabnak.com/books', 'iweb_book': 'https://www.islamweb.net/ar/library/index.php?page=bookcontents&ID=1',
     'manhal_rel': 'https://manhal.alkafeel.net/ar/reach_releases', 'noor_sitemap': 'https://noorlib.ir/sitemap.xml', 'noor_robots': 'https://noorlib.ir/robots.txt'}
for k, u in U.items():
    r = get(u, tries=2, timeout=40)
    st = r.status_code if r is not None else 0
    if r is not None: open(os.path.join(OUT, 'probe3', k + '.html'), 'wb').write(r.content[:3000000])
    log('probe', k, st, len(r.content) if r is not None else 0, r.url if r is not None else '')
