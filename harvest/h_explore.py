"""صفحه‌های نمونهٔ بیشتر برای کتابخانه‌های بعدی"""
import os
from hcommon import get, OUT, pmap
os.makedirs(os.path.join(OUT, 'samples2'), exist_ok=True)
U = {"ghaem_cat": "https://ghaemiyeh.com/category-page", "ghaem_multi": "https://ghaemiyeh.com/index.php/library/search/multi?q=%D9%82%D8%B1%D8%A2%D9%86",
     "rafed_cat3": "https://books.rafed.net/category/3", "rafed_cat3p2": "https://books.rafed.net/category/3?page=2",
     "safahat_p2": "https://www.safahat.org/books/2/", "safahat_book": "https://www.safahat.org/books/70920368/",
     "kadhim_p2": "https://www.imamkadhim.com/book/page/2/", "kadhim_posts": "https://www.imamkadhim.com/wp-json/wp/v2/book?per_page=2",
     "kadhim_types": "https://www.imamkadhim.com/wp-json/wp/v2/types",
     "ketabnak_list": "https://www.ketabnak.com/books", "ketabnak_book": "https://www.ketabnak.com/book/41380/x",
     "ketabnak_sitemap": "https://www.ketabnak.com/sitemap.xml",
     "iweb_lib2": "https://www.islamweb.net/ar/library/index.php?page=bookslist", "thaq_api": "https://thaqalaynlibrary.com/api/books",
     "noor_info": "https://noorlib.ir/book/info/3001", "waqf_book": "https://waqfeya.net/books/d3f72d55f7d94925b9f00e0f72a57036",
     "waqf_books_p3": "https://waqfeya.net/books?page=3&sortBy=newest", "waqf_api": "https://waqfeya.net/api/books?page=2",
     "gut_fa": "https://www.gutenberg.org/ebooks/search/?query=l.fa&submit_search=Go%21", "gut_ar": "https://www.gutenberg.org/ebooks/search/?query=l.ar",
     "alislam_books": "https://al-islam.org/library", "eshia_shn": "https://lib.eshia.ir/shenasnameh/26395", "efatwa_shn": "https://lib.efatwa.ir/shenasnameh/41821",
     "eshia_cat": "https://lib.eshia.ir/%D9%81%D9%82%D9%87"}
def one(k):
    r = get(U[k], tries=2)
    open(os.path.join(OUT, 'samples2', k + '.html'), 'wb').write(r.content if r is not None else b'')
    return k, (r.status_code if r is not None else 'ERR'), (len(r.content) if r is not None else 0)
res = pmap(one, list(U), 8)
open(os.path.join(OUT, 'samples2', '_index.txt'), 'w').write('\n'.join(map(str, res)))
