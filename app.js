/* کتابخانهٔ تلگرامی — Telegram Mini App (نسخهٔ اولیه با داده‌های واقعی) */
(function () {
  'use strict';

  var tg = window.Telegram && window.Telegram.WebApp;
  var app = document.getElementById('app');
  var HOME = null;           // data/home.json
  var MANIFEST = null;       // data/s/manifest.json
  var CV = null;             // bitmap of books with a downloaded cover (data/cv.json)
  var SAVED = [];            // [lite rows]
  var cache = {};
  var VER = (window.LIB_CONFIG && window.LIB_CONFIG.dataVersion) || '1';
  var COVERS = (window.LIB_CONFIG && window.LIB_CONFIG.coverBase) || '';

  // ---------- helpers ----------
  var FA = '۰۱۲۳۴۵۶۷۸۹';
  function fa(n) { return String(n == null ? '' : n).replace(/\d/g, function (d) { return FA[d]; }); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  // same rules as tools/build_data.py norm()
  function norm(t) {
    t = String(t || '').normalize('NFC').toLowerCase()
      .replace(/[يى]/g, 'ی').replace(/ك/g, 'ک').replace(/[ۀة]/g, 'ه')
      .replace(/[أإآ]/g, 'ا').replace(/ؤ/g, 'و').replace(/ئ/g, 'ی')
      .replace(/[ً-ْٰٔـ]/g, '')
      .replace(/[‌‍‎‏]/g, ' ')
      .replace(/[۰-۹]/g, function (d) { return String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d)); })
      .replace(/[٠-٩]/g, function (d) { return String('٠١٢٣٤٥٦٧٨٩'.indexOf(d)); });
    return t.replace(/[^\p{L}\p{N}\p{M}_]+/gu, ' ').replace(/\s+/g, ' ').trim();
  }
  var STOP = {}; 'و در از به با را که این آن یک یا تا بر برای های ها the of and a an in to on for'.split(' ').forEach(function (w) { STOP[w] = 1; });
  function fnv(t) {
    var b = new TextEncoder().encode(t), h = 0x811c9dc5;
    for (var i = 0; i < b.length; i++) { h ^= b[i]; h = Math.imul(h, 0x01000193) >>> 0; }
    return h >>> 0;
  }
  function splitNames(s) {
    return String(s || '').split(/\s*[،,؛;]\s*|\s+و\s+(?=\S+\s+\S+)/).map(function (x) { return x.trim(); })
      .filter(function (x) { return norm(x).length >= 3; });
  }
  var PALETTE = ['#7A2E2E', '#3B3561', '#2F4A3A', '#5B4A2F', '#1F4E5F', '#4A3B5C', '#6A3A4A', '#34505A', '#5A4632', '#2E3F66'];
  function colorFor(s) { var h = fnv(String(s)); return PALETTE[h % PALETTE.length]; }

  function getJSON(path) {
    if (cache[path]) return cache[path];
    var p = fetch('data/' + path + '?v=' + VER).then(function (r) {
      if (r.status === 404) return null;
      if (!r.ok) throw new Error(r.status);
      return r.json();
    });
    cache[path] = p;
    p.catch(function () { delete cache[path]; });
    return p;
  }
  function getWork(id) {
    var sh = HOME.shard;
    return getJSON('w/' + Math.floor(id / sh) + '.json').then(function (arr) { return arr && arr[id % sh]; });
  }
  function getPerson(name) {
    var n = norm(name);
    return getJSON('a/' + (fnv(n) % HOME.ashards) + '.json').then(function (d) { return d && d[n]; });
  }

  var ICON = {
    tg: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M21 4L3 11l6 2.5L11.5 20 15 15.5l4.5 3.5z"/><path d="M9 13.5L21 4"/></svg>',
    ext: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>',
    back: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg>',
    chev: '<svg class="chev" aria-hidden="true" viewBox="0 0 24 24"><path d="M14 6l-6 6 6 6"/></svg>',
    save: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M6 4h12v16l-6-4-6 4z"/></svg>',
    share: '<svg aria-hidden="true" viewBox="0 0 24 24"><circle cx="17" cy="6" r="2.5"/><circle cx="7" cy="12" r="2.5"/><circle cx="17" cy="18" r="2.5"/><path d="M9.2 10.8l5.6-3.3M9.2 13.2l5.6 3.3"/></svg>',
    books: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 4h4v16H5zM10 4h4v16h-4zM15.5 5l3.5-.8 3 15.6-3.6.8z"/></svg>',
    file: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/></svg>',
    search: '<svg aria-hidden="true" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/></svg>',
    img: '<svg aria-hidden="true" viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"/><circle cx="9.5" cy="9.5" r="1.5"/><path d="M20 15l-4.5-4.5L6 20"/></svg>',
    logo: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 6.5C10 5 7.5 4.5 4 4.5v13c3.5 0 6 .5 8 2 2-1.5 4.5-2 8-2v-13c-3.5 0-6 .5-8 2z"/><path d="M12 6.5v13"/></svg>'
  };

  // lite row: [id, title, author, translator, volume, copies, year]
  function L(r) { return { id: r[0], t: r[1], a: r[2] || '', tr: r[3] || '', v: r[4] || '', n: r[5] || 1, y: r[6] || '' }; }
  function volLabel(v) { if (!v) return ''; return /^(جلد|ج\.)/.test(v) ? v : 'جلد ' + v; }

  // covers: downloaded cover image (covers/<id/1000>/<id>.webp) over a default colour cover
  function hasCover(id) { return CV && id != null && id >= 0 && (CV[id >> 3] >> (id & 7)) & 1; }
  function coverHTML(b, size) {
    var t = b.t, a = b.a, v = volLabel(b.v);
    var img = hasCover(b.id) ? '<img alt="" decoding="async" src="' + COVERS + 'covers/' + Math.floor(b.id / 1000) + '/' + b.id + '.webp?v=' + VER + '" onload="this.parentNode.classList.add(\'has-img\')" onerror="this.remove()">' : '';
    return '<div class="cover c-' + size + '" role="img" aria-label="جلد ' + esc(t) + '"><div class="fb" style="background:' + colorFor(t) + '"><i></i><b>' +
      esc(t.length > 48 ? t.slice(0, 46) + '…' : t) + '</b><small>' + esc(v ? v + (a ? ' · ' + a : '') : a) + '</small></div>' + img + '</div>';
  }

  // ---------- storage ----------
  function loadSaved(cb) {
    var done = false;
    function finish(v) { if (done) return; done = true; try { SAVED = JSON.parse(v || '[]'); } catch (e) { SAVED = []; } if (!Array.isArray(SAVED)) SAVED = []; cb(); }
    var local = null; try { local = localStorage.getItem('lib_saved2'); } catch (e) {}
    try {
      if (tg && tg.CloudStorage && tg.isVersionAtLeast && tg.isVersionAtLeast('6.9')) {
        setTimeout(function () { finish(local); }, 1500);
        tg.CloudStorage.getItem('saved2', function (err, v) { finish(err ? local : (v || local)); });
        return;
      }
    } catch (e) {}
    finish(local);
  }
  function storeSaved() {
    var v = JSON.stringify(SAVED.slice(0, 300));
    try { if (tg && tg.CloudStorage && tg.isVersionAtLeast('6.9')) tg.CloudStorage.setItem('saved2', v.length < 4000 ? v : JSON.stringify(SAVED.slice(0, 40))); } catch (e) {}
    try { localStorage.setItem('lib_saved2', v); } catch (e) {}
  }
  function isSaved(id) { return SAVED.some(function (r) { return r[0] === id; }); }
  function toggleSaved(row) {
    var i = -1; SAVED.forEach(function (r, k) { if (r[0] === row[0]) i = k; });
    if (i >= 0) SAVED.splice(i, 1); else SAVED.unshift(row);
    storeSaved(); haptic('light');
  }

  // ---------- telegram ----------
  function haptic(k) { try { tg && tg.HapticFeedback && tg.HapticFeedback.impactOccurred(k); } catch (e) {} }
  function openLink(url) {
    if (!url) return;
    try {
      if (tg && tg.initData && /^https?:\/\/t\.me\//i.test(url)) { tg.openTelegramLink(url); return; }
      if (tg && tg.initData && tg.openLink) { tg.openLink(url); return; }
    } catch (e) {}
    window.open(url, '_blank', 'noopener');
  }
  function applyScheme() {
    var dark = tg && tg.colorScheme === 'dark';
    document.documentElement.classList.toggle('dark', !!dark);
    var c = dark ? '#072E33' : '#0E7480';
    try { tg.setHeaderColor(c); tg.setBackgroundColor(c); tg.setBottomBarColor && tg.setBottomBarColor(dark ? '#0E3F45' : '#FFFDF8'); } catch (e) {}
  }
  function setupTelegram() {
    if (!tg) return;
    try {
      tg.ready(); tg.expand(); applyScheme();
      tg.onEvent && tg.onEvent('themeChanged', applyScheme);
      tg.BackButton && tg.BackButton.onClick(function () { var b = document.querySelector('[data-back]'); b ? b.click() : go('#/'); });
    } catch (e) {}
  }
  function go(h) { location.hash = h; }

  // ---------- shared view pieces ----------
  function shelf(rows, size) {
    return '<div class="shelf' + (size === 'sm' ? ' sm' : '') + '">' + rows.map(function (r) {
      var b = L(r);
      return '<a href="#/b/' + b.id + '">' + coverHTML(b, size || 'md') +
        '<span class="t">' + esc(b.t) + '</span><span class="a">' + esc(b.a || volLabel(b.v)) + '</span></a>';
    }).join('') + '</div>';
  }
  function rowHTML(r, role) {
    var b = L(r);
    var sub = role || [b.a, b.tr ? 'ترجمهٔ ' + b.tr : ''].filter(Boolean).join(' · ');
    var meta = [volLabel(b.v), b.y ? fa(b.y) : ''].filter(Boolean).join(' · ');
    return '<a class="row" href="#/b/' + b.id + '">' + coverHTML(b, 'xs') +
      '<div class="grow"><span class="nm" style="font-weight:700;font-size:15px">' + esc(b.t) + '</span>' +
      (sub ? '<span class="sub">' + esc(sub) + '</span>' : '') + (meta ? '<span class="sub">' + esc(meta) + '</span>' : '') +
      (b.n > 1 ? '<span class="badge">' + fa(b.n) + ' نسخه در کانال‌ها</span>' : '') + '</div>' + ICON.chev + '</a>';
  }
  function bar(extra) {
    return '<div class="bar"><a class="icon-btn" href="#/" data-back aria-label="بازگشت">' + ICON.back + '</a>' + (extra || '') + '</div>';
  }
  function loading() { return '<div class="loading">در حال بارگذاری…</div>'; }
  function failed() { return '<div class="empty">بارگذاری ممکن نشد. اتصال را بررسی کنید و دوباره امتحان کنید.</div>'; }
  function channelRow(ch, i) {
    return '<a class="row" href="#/c/' + i + '"><div class="dot">' + ICON.books + '</div><div class="grow"><span class="nm">' + esc(ch.name) + '</span>' +
      '<span class="sub">' + fa(ch.w.toLocaleString('en')) + ' کتاب' + (ch.handle ? ' · ' + esc(ch.handle) : '') + '</span></div>' + ICON.chev + '</a>';
  }
  var navToken = 0;
  function render(html, tab, sub) {
    app.innerHTML = html;
    window.scrollTo(0, 0);
    [].forEach.call(document.querySelectorAll('.tabbar a'), function (a) {
      var on = a.getAttribute('data-tab') === tab;
      a.classList.toggle('on', on);
      if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
    try { if (tg && tg.BackButton) { sub ? tg.BackButton.show() : tg.BackButton.hide(); } } catch (e) {}
    return ++navToken;
  }
  function stale(tok) { return tok !== navToken; }

  // ---------- views ----------
  function viewHome() {
    var h = HOME;
    var day = Math.floor(Date.now() / 864e5);
    var feat = h.featured.length ? h.featured[day % h.featured.length] : null;
    var chans = h.channels.map(function (c, i) { return [c, i]; }).sort(function (a, b) { return b[0].w - a[0].w; }).slice(0, 6);
    var html = '<header class="top"><div class="brand"><div class="logo">' + ICON.logo + '</div><div><h1>کتابخانه</h1>' +
      '<p>' + fa(h.nworks.toLocaleString('en')) + ' کتاب از ' + fa(h.channels.length) + ' کانال</p></div></div>' +
      '<a class="icon-btn" href="#/saved" aria-label="نشان‌شده‌ها">' + ICON.save + '</a></header>' +
      '<a class="search" href="#/s" role="search" aria-label="جستجو در کتابخانه">' + ICON.search + '<span style="color:var(--muted);font-size:15px">عنوان، نویسنده، مترجم یا ناشر…</span></a>' +
      '<nav class="chips" aria-label="دسته‌ها">' + h.cats.filter(function (c) { return c.k !== 'x'; }).map(function (c) {
        return '<a class="chip" href="#/k/' + c.k + '">' + esc(c.name) + '</a>';
      }).join('') + '</nav>' +
      '<section class="sec"><div class="sec-head"><h2>از هر دسته</h2><a href="#/categories">همهٔ دسته‌ها</a></div><div id="mix">' + shelf(h.recent.slice(0, 12)) + '</div></section>' +
      (feat ? '<section class="sec"><div class="sec-head"><h2>پیشنهاد امروز</h2></div><div id="feat">' + '<div class="card list">' + rowHTML(feat) + '</div></div></section>' : '') +
      '<section class="sec"><div class="sec-head"><h2>مرور بر اساس کانال</h2><a href="#/channels">همهٔ کانال‌ها</a></div><div class="card list">' +
      chans.map(function (x) { return channelRow(x[0], x[1]); }).join('') + '</div></section>';
    var tok = render(html, 'home');
    randomMix().then(function (items) {
      if (stale(tok) || !items.length) return;
      document.getElementById('mix').innerHTML = '<div class="shelf">' + items.map(function (x) {
        var b = L(x.r);
        return '<a href="#/b/' + b.id + '">' + coverHTML(b, 'md') + '<span class="t">' + esc(b.t) + '</span>' +
          '<span class="a" style="color:var(--gold)">' + esc(x.cat.name) + '</span></a>';
      }).join('') + '</div>';
    });
    if (feat) getWork(feat[0]).then(function (w) { if (!stale(tok) && w) document.getElementById('feat').innerHTML = featCard(feat[0], w); });
  }
  // one random book from each category (prefers books with a cover); new picks on every visit
  function rnd(n) { return Math.floor(Math.random() * n); }
  function randomMix() {
    var cats = HOME.cats.filter(function (c) { return c.k !== 'x' && c.n > 0; });
    return Promise.all(cats.map(function (c) {
      var pages = Math.max(1, Math.ceil(c.n / HOME.page));
      return getJSON('k/' + c.k + '/' + rnd(pages) + '.json').then(function (rows) {
        if (!rows || !rows.length) return null;
        var pool = rows.filter(function (r) { return hasCover(r[0]); });
        if (!pool.length) pool = rows;
        return { r: pool[rnd(pool.length)], cat: c };
      }).catch(function () { return null; });
    })).then(function (list) {
      list = list.filter(Boolean);
      for (var i = list.length - 1; i > 0; i--) { var j = rnd(i + 1), t = list[i]; list[i] = list[j]; list[j] = t; }
      return list;
    });
  }
  function featCard(id, w) {
    var c = w.c[0], ch = HOME.channels[c.ch] || {};
    var b = { id: id, t: w.t, a: w.a || '', v: w.v || '' };
    return '<article class="card feat"><div class="feat-top"><a href="#/b/' + id + '">' + coverHTML(b, 'xs').replace('c-xs"', 'c-xs" style="width:84px;height:120px"') + '</a>' +
      '<dl class="kv"><dt>عنوان</dt><dd style="font-weight:700"><a href="#/b/' + id + '" style="color:inherit">' + esc(w.t) + '</a></dd>' +
      (w.a ? '<dt>پدیدآور</dt><dd>' + peopleLinks(w.a) + '</dd>' : '') +
      (w.tr ? '<dt>مترجم</dt><dd>' + peopleLinks(w.tr) + '</dd>' : '') +
      (c.p ? '<dt>ناشر</dt><dd>' + esc(c.p) + '</dd>' : '') + (c.y ? '<dt>سال</dt><dd>' + fa(c.y) + '</dd>' : '') +
      '<dt>کانال</dt><dd>' + esc(ch.name || '') + '</dd></dl></div>' +
      '<button class="primary in-card" data-open="' + esc(c.l || '') + '"' + (c.l ? '' : ' disabled') + '>' + ICON.tg + (c.l ? 'خواندن در تلگرام' : 'پیوند عمومی ندارد') + '</button></article>';
  }
  function peopleLinks(s) {
    var parts = splitNames(s);
    if (!parts.length) return esc(s);
    return parts.map(function (p) { return '<a href="#/a/' + encodeURIComponent(p) + '">' + esc(p) + '</a>'; }).join('، ');
  }

  function viewBook(id) {
    id = +id;
    var tok = render(bar() + loading(), null, true);
    getWork(id).then(function (w) {
      if (stale(tok)) return;
      if (!w) return render(bar() + '<div class="empty">این کتاب پیدا نشد.</div>', null, true);
      var c0 = w.c[0], ch0 = HOME.channels[c0.ch] || {};
      var f = w.f || null, fm = w.fm || 0;
      var lite = [id, w.t, w.a || '', w.tr || '', w.v || '', w.c.length, w.y || ''];
      var saved = isSaved(id);
      var meta = [c0.p, c0.y && fa(c0.y), c0.pg && fa(c0.pg) + ' صفحه'].filter(Boolean).join(' · ');
      var h = bar('<div class="grp"><button class="icon-btn" id="share" aria-label="هم‌رسانی">' + ICON.share + '</button>' +
        '<button class="icon-btn' + (saved ? ' on' : '') + '" id="save" aria-label="' + (saved ? 'برداشتن نشان' : 'نشان کردن') + '">' + ICON.save + '</button></div>');
      h += '<section class="hero">' + coverHTML({ id: id, t: w.t, a: w.a || '', v: w.v || '' }, 'lg') +
        '<div style="display:flex;flex-direction:column;gap:6px;align-items:center"><h1>' + esc(w.t) + '</h1>' +
        (w.st ? '<p style="font-size:14px;color:var(--on-bg)">' + esc(w.st) + '</p>' : '') +
        (w.v ? '<p>' + esc(volLabel(w.v)) + '</p>' : '') +
        (w.a ? '<span class="by">' + peopleLinks(w.a) + '</span>' : '') +
        (w.tr ? '<span class="by" style="font-size:13px">ترجمهٔ ' + peopleLinks(w.tr) + '</span>' : '') +
        (w.e ? '<p>' + esc(w.e) + '</p>' : '') +
        (meta ? '<p>' + esc(meta) + '</p>' : '') + '</div>' +
        (c0.cv ? '<button class="ghost-btn" style="color:var(--gold);border-color:var(--gold)" data-open="' + esc(c0.cv === 1 ? c0.l : c0.cv) + '">' + ICON.img + 'دیدن جلد در کانال</button>' : '') +
        '</section>';
      h += '<section class="sec px" style="gap:10px"><button class="primary" data-open="' + esc(c0.l || '') + '"' + (c0.l ? '' : ' disabled') + '>' + ICON.tg +
        (c0.l ? 'خواندن در تلگرام' : 'پیوند عمومی ندارد') + '</button>' +
        '<p class="muted" style="margin:0;text-align:center;font-size:12px">' + esc(['کانال اصلی: ' + (ch0.name || '—'), 'PDF', c0.sz ? fa(c0.sz) + ' مگابایت' : '', c0.d ? fa(c0.d) : ''].filter(Boolean).join(' · ')) + '</p>' +
        (c0.note ? '<p class="muted" style="margin:0;text-align:center;font-size:12px;line-height:1.8">' + esc(c0.note) + '</p>' : '') + '</section>';
      var alts = w.c.slice(1);
      if (alts.length) {
        h += '<section class="sec"><div class="px" style="display:flex;flex-direction:column;gap:4px"><h2>نسخه‌های دیگر (' + fa(alts.length) + ')</h2>' +
          '<p class="muted" style="margin:0;font-size:13px;line-height:1.7">همین کتاب در کانال‌های دیگر یا پست‌های دیگر. اگر پیوند اصلی باز نشد، از این‌ها استفاده کنید.</p></div>' +
          '<div class="card list">' + alts.slice(0, 30).map(function (a) {
            var ch = HOME.channels[a.ch] || {};
            var diff = (a.p && c0.p && a.p !== c0.p) || (a.y && c0.y && a.y !== c0.y);
            var same = a.ch === c0.ch;
            var m = ['PDF', a.sz ? fa(a.sz) + ' مگابایت' : '', [a.p, a.y && fa(a.y)].filter(Boolean).join('، '), a.d ? fa(a.d) : ''].filter(Boolean).join(' · ');
            return '<div class="row"><div class="dot">' + ICON.file + '</div><div class="grow"><div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap"><span class="nm">' + esc(ch.name || 'کانال') + '</span>' +
              (diff ? '<span class="badge warn">چاپ دیگر</span>' : '') + (same ? '<span class="badge">همان کانال</span>' : '') + '</div><span class="sub">' + esc(m) + '</span></div>' +
              '<button class="ghost-btn" data-open="' + esc(a.l || '') + '"' + (a.l ? '' : ' disabled') + ' aria-label="باز کردن نسخهٔ ' + esc(ch.name || '') + '">باز کردن' + ICON.ext + '</button></div>';
          }).join('') + '</div>' + (alts.length > 30 ? '<p class="muted px" style="margin:0;font-size:12px">و ' + fa(alts.length - 30) + ' نسخهٔ دیگر</p>' : '') + '</section>';
      }
      var rec = [];
      if (f) {
        rec = [['سرشناسه', f.h], ['عنوان و پدیدآور', f.ta], ['مشخصات نشر', f.pub], ['مشخصات ظاهری', f.phys], ['شابک', f.isbn || c0.isbn],
          ['وضعیت ویراست', f.edn], ['عنوان اصلی', f.orig], ['موضوع', f.subj], ['شناسهٔ افزوده', f.add],
          ['ردهٔ کنگره', f.lc], ['ردهٔ دیویی', f.dw], ['ش. کتابشناسی ملی', f.nl]];
      } else {
        rec = [['عنوان', w.t], ['پدیدآور', w.a], ['مترجم', w.tr], ['ناشر', c0.p], ['سال نشر', c0.y && fa(c0.y)], ['نوبت چاپ', c0.ed],
          ['شمار صفحات', c0.pg && fa(c0.pg)], ['شابک', c0.isbn], ['موضوع', w.tag], ['زبان', w.lang]];
      }
      rec = rec.filter(function (x) { return x[1]; });
      var label = f ? (fm === 2 ? 'فیپا · تطبیق قطعی' : fm === 1 ? 'فیپا · تطبیق محتمل' : 'فیپا · تطبیق احتمالی') : 'از کپشن کانال';
      if (rec.length) {
        h += '<section class="sec"><div class="sec-head"><h2>مشخصات کتاب‌شناختی</h2><span class="muted" style="font-size:12px">' + label + '</span></div>' +
          (f && fm === 0 ? '<div class="notice">این رکورد فقط از روی عنوان پیدا شده و ممکن است مربوط به کتاب یا چاپ دیگری باشد.</div>' : '') +
          '<dl class="card rec">' + rec.map(function (x) { return '<div><dt>' + x[0] + '</dt><dd>' + esc(x[1]) + '</dd></div>'; }).join('') + '</dl>';
        var subj = f && f.subj ? f.subj.split(/\s*[؛|]\s*/).filter(Boolean).slice(0, 6) : [];
        var cat = HOME.cats.filter(function (c) { return c.k === w.k; })[0];
        if (subj.length || cat) h += '<div class="tags">' + (cat ? '<a class="tag" href="#/k/' + cat.k + '" style="background:var(--gold);color:var(--on-gold)">' + esc(cat.name) + '</a>' : '') +
          subj.map(function (s) { var q = s.split('--')[0].trim(); return '<a class="tag" href="#/s/' + encodeURIComponent(q) + '">' + esc(s) + '</a>'; }).join('') + '</div>';
        h += '</section>';
      }
      var firstAuthor = splitNames(w.a)[0];
      if (firstAuthor) h += '<section class="sec" id="more"></section>';
      h += '<p class="muted" style="text-align:center;font-size:11px;margin:0">شناسهٔ کتاب: ' + fa(id) + '</p>';
      tok = render(h, null, true);
      document.getElementById('save').onclick = function () { toggleSaved(lite); var b = this; var on = isSaved(id); b.classList.toggle('on', on); b.setAttribute('aria-label', on ? 'برداشتن نشان' : 'نشان کردن'); };
      document.getElementById('share').onclick = function () {
        var bot = (window.LIB_CONFIG && window.LIB_CONFIG.botUsername) || '';
        var url = bot ? 'https://t.me/' + bot + '?startapp=b' + id : location.href;
        openLink('https://t.me/share/url?url=' + encodeURIComponent(url) + '&text=' + encodeURIComponent(w.t + (w.a ? ' — ' + w.a : '')));
      };
      if (firstAuthor) getPerson(firstAuthor).then(function (p) {
        if (stale(tok) || !p) return;
        var more = p.o.concat(p.r).filter(function (r) { return r[0] !== id; }).slice(0, 15);
        if (more.length) document.getElementById('more').innerHTML = '<div class="sec-head"><h2>از همین نویسنده</h2><a href="#/a/' + encodeURIComponent(firstAuthor) + '">همه</a></div>' + shelf(more, 'sm');
      });
    }).catch(function () { if (!stale(tok)) render(bar() + failed(), null, true); });
  }

  function viewAuthor(name, filter) {
    filter = filter || 0;
    var tok = render(bar() + loading(), null, true);
    getPerson(name).then(function (p) {
      if (stale(tok)) return;
      if (!p) return render(bar() + '<div class="empty">برای «' + esc(name) + '» صفحه‌ای پیدا نشد.</div>', null, true);
      var chs = {};
      var shown = filter === 1 ? p.o : filter === 2 ? p.r : p.o.concat(p.r);
      var h = bar() + '<section class="hero"><div class="avatar" aria-hidden="true">' + esc(p.n.trim().charAt(0)) + '</div>' +
        '<h1 style="font-size:28px">' + esc(p.n) + '</h1>' +
        '<div class="card stats" style="margin:0"><div><b>' + fa(p.no) + '</b><span>تألیف</span></div><div><b>' + fa(p.nr) + '</b><span>ترجمه</span></div><div><b>' + fa(p.no + p.nr) + '</b><span>همه</span></div></div></section>' +
        '<div class="seg" role="group" aria-label="نوع اثر">' + ['همه', 'تألیف', 'ترجمه'].map(function (l, i) {
          return '<button data-f="' + i + '" aria-pressed="' + (i === filter) + '">' + l + '</button>';
        }).join('') + '</div>' +
        '<section class="sec"><div class="card list">' + (shown.length ? shown.map(function (r) {
          var b = L(r);
          return rowHTML(r, filter === 2 || (filter === 0 && p.r.indexOf(r) >= 0) ? 'ترجمه' + (b.a ? ' · اثر ' + b.a : '') : 'تألیف');
        }).join('') : '<div class="empty" style="color:var(--muted)">موردی نیست.</div>') + '</div>' +
        ((filter !== 2 && p.no > p.o.length) || (filter !== 1 && p.nr > p.r.length) ? '<p class="muted px" style="font-size:12px;margin:0">فقط ۴۰۰ مورد نخست نمایش داده می‌شود.</p>' : '') + '</section>';
      render(h, null, true);
      [].forEach.call(document.querySelectorAll('.seg button'), function (b) {
        b.onclick = function () { haptic('light'); viewAuthor(name, +b.getAttribute('data-f')); };
      });
    }).catch(function () { if (!stale(tok)) render(bar() + failed(), null, true); });
  }

  // ---------- search ----------
  function shardKey(tk) {
    var p2 = tk.slice(0, 2);
    return MANIFEST.split.indexOf(p2) >= 0 && tk.length > 2 ? tk.slice(0, 3) : p2;
  }
  function shardFile(key) {
    var s = 'x'; for (var i = 0; i < key.length; i++) s += key.charCodeAt(i).toString(16) + '-';
    return 's/' + s + '.json';
  }
  function doSearch(q) {
    var words = norm(q).split(' ').filter(function (w) { return w.length >= 2 && !STOP[w]; });
    if (!words.length) return Promise.resolve(null);
    return Promise.all(words.map(function (wd) { return getJSON(shardFile(shardKey(wd))); })).then(function (shards) {
      var lite = {}, sets = [];
      shards.forEach(function (sh, k) {
        var wd = words[k], ids = {};
        if (sh) {
          sh.w.forEach(function (r) { lite[r[0]] = r; });
          var last = k === words.length - 1;
          Object.keys(sh.t).forEach(function (tk) {
            if (tk === wd || (last && tk.indexOf(wd) === 0)) sh.t[tk].forEach(function (i) { ids[i] = (ids[i] || 0) + (tk === wd ? 2 : 1); });
          });
        }
        sets.push(ids);
      });
      var base = sets[0], out = [];
      Object.keys(base).forEach(function (i) {
        var sc = 0;
        for (var k = 0; k < sets.length; k++) { if (!sets[k][i]) return; sc += sets[k][i]; }
        var r = lite[i], tn = norm(r[1]);
        if (tn === norm(q)) sc += 20; else if (tn.indexOf(norm(q)) === 0) sc += 8;
        words.forEach(function (wd) { if ((' ' + tn + ' ').indexOf(' ' + wd) >= 0) sc += 3; });
        sc += Math.min(r[5] || 1, 5) * 0.3;
        out.push([sc, r]);
      });
      out.sort(function (a, b) { return b[0] - a[0] || a[1][1].length - b[1][1].length; });
      return out.map(function (x) { return x[1]; });
    });
  }
  function viewSearch(initial) {
    var h = '<form class="search" role="search" onsubmit="return false" style="margin-top:4px"><label for="q" class="sr">جستجو در کتابخانه</label>' + ICON.search +
      '<input id="q" type="search" autocomplete="off" placeholder="عنوان، نویسنده، مترجم یا ناشر…" enterkeyhint="search" value="' + esc(initial || '') + '"></form>' +
      '<section class="sec"><p class="muted px" id="cnt" style="margin:0;font-size:12px"></p><div class="card list" id="res"></div></section>';
    render(h, 'search');
    var q = document.getElementById('q'), res = document.getElementById('res'), cnt = document.getElementById('cnt');
    var timer, seq = 0, LIMIT = 80;
    function show(rows, n) {
      res.innerHTML = rows.slice(0, n).map(function (r) { return rowHTML(r); }).join('') +
        (rows.length > n ? '<button class="ghost-btn" id="more" style="margin:12px auto;display:flex">نمایش بیشتر</button>' : '');
      var m = document.getElementById('more');
      if (m) m.onclick = function () { show(rows, n + LIMIT); };
    }
    function run() {
      var v = q.value, my = ++seq;
      try { history.replaceState(null, '', '#/s/' + encodeURIComponent(v)); } catch (e) {}
      if (!norm(v)) { cnt.textContent = ''; res.innerHTML = '<div class="empty" style="color:var(--muted)">نام کتاب، نویسنده، مترجم یا ناشر را بنویسید.</div>'; return; }
      cnt.textContent = 'در حال جستجو…';
      doSearch(v).then(function (rows) {
        if (my !== seq) return;
        rows = rows || [];
        cnt.textContent = rows.length ? fa(rows.length.toLocaleString('en')) + ' نتیجه' : '';
        if (!rows.length) { res.innerHTML = '<div class="empty" style="color:var(--muted)">چیزی پیدا نشد.</div>'; return; }
        show(rows, LIMIT);
      }).catch(function () { if (my === seq) { cnt.textContent = ''; res.innerHTML = failed(); } });
    }
    q.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(run, 300); });
    run();
    if (!initial) setTimeout(function () { q.focus(); }, 60);
  }

  // ---------- paged lists ----------
  function viewPaged(title, sub, dir, total, tab, extraTop) {
    var page = 0, pages = Math.ceil(total / HOME.page);
    var h = bar() + '<section class="sec"><div class="sec-head"><h2 style="font-size:22px">' + esc(title) + '</h2><span class="muted" style="font-size:13px">' + fa(total.toLocaleString('en')) + ' کتاب</span></div>' +
      (sub ? '<p class="muted px" style="margin:0;font-size:12px">' + esc(sub) + '</p>' : '') + (extraTop || '') +
      '<div class="card list" id="list"></div><button class="ghost-btn" id="more" style="margin:0 auto;display:none;color:var(--gold);border-color:var(--gold)">نمایش بیشتر</button></section>';
    var tok = render(h, tab || null, true);
    var list = document.getElementById('list'), more = document.getElementById('more');
    function load() {
      more.disabled = true; more.textContent = 'در حال بارگذاری…';
      getJSON(dir + '/' + page + '.json').then(function (rows) {
        if (stale(tok)) return;
        list.insertAdjacentHTML('beforeend', (rows || []).map(function (r) { return rowHTML(r); }).join(''));
        page++;
        more.style.display = page < pages ? 'flex' : 'none'; more.disabled = false; more.textContent = 'نمایش بیشتر';
      }).catch(function () { more.disabled = false; more.textContent = 'دوباره امتحان کنید'; more.style.display = 'flex'; });
    }
    more.onclick = load;
    if (total) load(); else list.innerHTML = '<div class="empty" style="color:var(--muted)">کتابی نیست.</div>';
  }
  function viewChannel(i) {
    var ch = HOME.channels[+i]; if (!ch) return viewMissing();
    viewPaged(ch.name, [ch.handle, fa(ch.n.toLocaleString('en')) + ' فایل PDF'].filter(Boolean).join(' · '), 'c/' + i, ch.w, null,
      ch.link ? '<div class="px"><button class="primary" data-open="' + esc(ch.link) + '">' + ICON.tg + 'رفتن به کانال</button></div>' : '');
  }
  function viewCat(k) {
    var c = HOME.cats.filter(function (x) { return x.k === k; })[0]; if (!c) return viewMissing();
    viewPaged(c.name, k === 'x' ? 'کتاب‌هایی که ردهٔ دیویی قطعی ندارند' : 'بر پایهٔ ردهٔ دیویی فیپا', 'k/' + k, c.n, 'categories');
  }
  function viewChannels() {
    var all = HOME.channels.map(function (c, i) { return [c, i]; }).sort(function (a, b) { return b[0].w - a[0].w; });
    render(bar() + '<section class="sec"><div class="sec-head"><h2 style="font-size:22px">کانال‌ها</h2></div><div class="card list">' +
      all.map(function (x) { return channelRow(x[0], x[1]); }).join('') + '</div></section>', null, true);
  }
  function viewCategories() {
    render('<section class="sec"><div class="sec-head"><h2 style="font-size:22px">دسته‌ها</h2></div><div class="grid">' +
      HOME.cats.map(function (c) { return '<a href="#/k/' + c.k + '"><b>' + esc(c.name) + '</b><span>' + fa(c.n.toLocaleString('en')) + ' کتاب</span></a>'; }).join('') +
      '</div><p class="muted px" style="margin:0;font-size:12px;line-height:1.8">دسته‌ها از ردهٔ دیویی و موضوع کتابخانهٔ ملی (تطبیق‌های قطعی و محتمل) ساخته شده‌اند؛ برای «ادبیات داستانی»، «شعر و دیوان» و «فقه و حقوق» از عنوان و برچسب کانال‌ها هم کمک گرفته شده است.</p></section>' +
      '<section class="sec"><div class="sec-head"><h2>کانال‌ها</h2><a href="#/channels">همه</a></div><div class="card list">' +
      HOME.channels.map(function (c, i) { return [c, i]; }).sort(function (a, b) { return b[0].w - a[0].w; }).slice(0, 8)
        .map(function (x) { return channelRow(x[0], x[1]); }).join('') + '</div></section>', 'categories');
  }
  function viewSaved() {
    render('<section class="sec"><div class="sec-head"><h2 style="font-size:22px">نشان‌شده‌ها</h2></div>' +
      (SAVED.length ? '<div class="card list">' + SAVED.map(function (r) { return rowHTML(r); }).join('') + '</div>' :
        '<div class="empty">هنوز کتابی نشان نکرده‌اید. در صفحهٔ هر کتاب، دکمهٔ نشان را بزنید.</div>') + '</section>', 'saved');
  }
  function viewMissing() { render(bar() + '<div class="empty">این صفحه پیدا نشد.</div>', null, true); }

  // ---------- clicks ----------
  var depth = 0;
  window.addEventListener('hashchange', function () { depth++; });
  document.addEventListener('click', function (e) {
    var bk = e.target.closest && e.target.closest('[data-back]');
    if (bk) { e.preventDefault(); if (depth > 0) { depth -= 2; history.back(); } else go('#/'); return; }
    var b = e.target.closest && e.target.closest('[data-open]');
    if (b && !b.disabled && b.getAttribute('data-open')) { e.preventDefault(); haptic('medium'); openLink(b.getAttribute('data-open')); }
  });

  // ---------- router ----------
  function route() {
    var raw = (location.hash || '#/').slice(1), h;
    try { h = decodeURIComponent(raw); } catch (e) { h = raw; }
    var p = h.split('/').filter(Boolean);
    var rest = p.slice(1).join('/');
    switch (p[0]) {
      case undefined: return viewHome();
      case 'b': return viewBook(p[1]);
      case 'a': return viewAuthor(rest);
      case 'c': return viewChannel(p[1]);
      case 'channels': return viewChannels();
      case 'k': return viewCat(p[1]);
      case 'categories': return viewCategories();
      case 's': return viewSearch(rest);
      case 'saved': return viewSaved();
      default: return viewMissing();
    }
  }

  // ---------- boot ----------
  setupTelegram();
  // Telegram launch data arrives in the hash (#tgWebAppData=…); the SDK has already read it.
  if (!/^#\//.test(location.hash)) history.replaceState(null, '', location.pathname + location.search + '#/');
  Promise.all([getJSON('home.json'), getJSON('s/manifest.json'), fetch(COVERS + 'cv.json?v=' + VER).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })]).then(function (r) {
    HOME = r[0]; MANIFEST = r[1] || { split: [] };
    if (r[2] && r[2].b) { try { var bin = atob(r[2].b); CV = new Uint8Array(bin.length); for (var i = 0; i < bin.length; i++) CV[i] = bin.charCodeAt(i); } catch (e) { CV = null; } }
    loadSaved(function () {
      var start = tg && tg.initDataUnsafe && tg.initDataUnsafe.start_param;
      if (start && /^b\d+$/.test(start)) history.replaceState(null, '', '#/b/' + start.slice(1));
      window.addEventListener('hashchange', route);
      route();
    });
  }).catch(function () {
    app.innerHTML = '<div class="empty">بارگذاری کتابخانه ممکن نشد. لطفاً دوباره امتحان کنید.</div>';
  });
})();
