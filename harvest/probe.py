"""Check which library sites answer from the GitHub runner; writes ../out/probe.txt"""
import requests, concurrent.futures as cf
SITES = ["https://shamela.ws/book/6387", "https://lib.eshia.ir/", "https://pdf.lib.eshia.ir/", "https://lib.efatwa.ir/",
 "https://noorlib.ir/", "https://www.ghbook.ir/", "https://ghaemiyeh.com/", "https://waqfeya.net/", "https://www.islamweb.net/ar/library/",
 "https://al-islam.org/", "https://www.shiaonlinelibrary.com/", "https://www.imamkadhim.com/book/", "https://thaqalaynlibrary.com/",
 "https://library.tebyan.net/", "https://fa.wikisource.org/", "https://api.ganjoor.net/api/ganjoor/poets", "https://www.ketabnak.com/",
 "https://dl.nlai.ir/", "https://dlib.ical.ir/", "https://digital.aqr.ir/", "https://utdlib.ut.ac.ir/", "https://www.safahat.org/books/",
 "https://archive.org/advancedsearch.php?q=language:per&rows=1&output=json", "https://openlibrary.org/search.json?q=language:per&limit=1",
 "https://www.gutenberg.org/ebooks/", "https://www.hathitrust.org/", "https://gallica.bnf.fr/", "https://www.googleapis.com/books/v1/volumes?q=hafez",
 "https://dashboard.aqaed.net/api/v1/singleBooks/10560", "https://manhal.alkafeel.net/", "https://alkafeel.net/library/", "https://hawzah.net/fa/Book/List",
 "https://books.rafed.net/view/350", "https://files.turath.io/data-v3.json", "https://api.usul.ai/total", "https://pdf.al-mostafa.com/", "https://dorar.net/",
 "https://raw.githubusercontent.com/OpenITI/RELEASE/master/README.md"]
def chk(u):
    try:
        r = requests.get(u, timeout=40, headers={"User-Agent": "Mozilla/5.0 library-miniapp"})
        return f"{r.status_code}\t{len(r.content)}\t{u}"
    except Exception as e:
        return f"ERR\t{type(e).__name__}\t{u}"
with cf.ThreadPoolExecutor(12) as ex:
    res = list(ex.map(chk, SITES))
open("../out/probe.txt", "w").write("\n".join(res) + "\n")
print("\n".join(res))
