"""Save sample pages of each library for parser development -> ../out/samples/"""
import os, re, requests, concurrent.futures as cf
os.makedirs("../out/samples", exist_ok=True)
U = {
 "shamela_cat1": "https://shamela.ws/category/1", "shamela_book": "https://shamela.ws/book/6387",
 "shamela_home": "https://shamela.ws/",
 "eshia_home": "https://lib.eshia.ir/", "eshia_all": "https://lib.eshia.ir/all", "eshia_book": "https://lib.eshia.ir/26395/1/0",
 "eshia_bookroot": "https://lib.eshia.ir/26395",
 "eshiapdf_home": "https://pdf.lib.eshia.ir/", "eshiapdf_book": "https://pdf.lib.eshia.ir/94335/1/1", "eshiapdf_all": "https://pdf.lib.eshia.ir/all",
 "efatwa_home": "https://lib.efatwa.ir/", "efatwa_all": "https://lib.efatwa.ir/all", "efatwa_book": "https://lib.efatwa.ir/41821/1/13",
 "efatwapdf_home": "https://pdf.lib.efatwa.ir/", "efatwapdf_all": "https://pdf.lib.efatwa.ir/all",
 "ghaem_home": "https://ghaemiyeh.com/", "ghaem_book": "https://ghaemiyeh.com/show-book/682985", "ghaem_lib": "https://ghaemiyeh.com/library",
 "rafed_home": "https://books.rafed.net/", "rafed_book": "https://books.rafed.net/view/350",
 "safahat_list": "https://www.safahat.org/books/", "safahat_list2": "https://www.safahat.org/books/?page=2", "safahat_book": "https://www.safahat.org/books/70920368/",
 "kadhim_list": "https://www.imamkadhim.com/book/", "kadhim_wpjson": "https://www.imamkadhim.com/wp-json/wp/v2/types",
 "manhal_search": "https://manhal.alkafeel.net/search?types%5B%5D=%D9%83%D8%AA%D8%A8", "manhal_bib": "https://manhal.alkafeel.net/bibliography/1018",
 "manhal_releases": "https://manhal.alkafeel.net/ar/reach_releases",
 "waqf_books2": "https://waqfeya.net/books?page=2", "waqf_cats": "https://waqfeya.net/categories", "waqf_robots": "https://waqfeya.net/sitemap.xml",
 "iweb_lib": "https://www.islamweb.net/ar/library/", "iweb_content": "https://www.islamweb.net/ar/library/content/301/157/",
 "iweb_pdf": "https://www.islamweb.net/ar/library/index.php?page=pdf",
 "ketabnak_home": "https://www.ketabnak.com/", "thaqalayn_home": "https://thaqalaynlibrary.com/",
 "noor_list_api": "https://noorlib.ir/sitemap.xml", "ghaem_sitemap": "https://ghaemiyeh.com/sitemap.xml",
 "rafed_sitemap": "https://books.rafed.net/sitemap.xml", "shamela_sitemap": "https://shamela.ws/sitemap.xml",
 "hawzah_list": "https://hawzah.net/fa/Book/List?pN=1", "aqaed_list": "https://dashboard.aqaed.net/api/v1/books?page=1",
 "gutenberg_fa": "https://www.gutenberg.org/ebooks/search/?query=l.fa", "ol_fa": "https://openlibrary.org/search.json?q=language:per&has_fulltext=true&limit=5",
 "ia_fa": "https://archive.org/advancedsearch.php?q=language%3A%28per+OR+Persian%29+AND+mediatype%3Atexts&fl%5B%5D=identifier&rows=0&output=json",
 "ia_ar": "https://archive.org/advancedsearch.php?q=language%3A%28ara+OR+Arabic%29+AND+mediatype%3Atexts&fl%5B%5D=identifier&rows=0&output=json",
}
def get(k):
    try:
        r = requests.get(U[k], timeout=60, headers={"User-Agent": "Mozilla/5.0 (library-miniapp)"})
        open(f"../out/samples/{k}.html", "wb").write(r.content)
        return f"{k}\t{r.status_code}\t{len(r.content)}\t{r.url}"
    except Exception as e:
        return f"{k}\tERR\t{e}"
with cf.ThreadPoolExecutor(10) as ex:
    res = list(ex.map(get, U))
open("../out/samples/_index.txt", "w").write("\n".join(res) + "\n")
print("\n".join(res))
