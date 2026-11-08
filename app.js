/* کتابخانهٔ تلگرامی — Telegram Mini App */
(function () {
  'use strict';

  var tg = window.Telegram && window.Telegram.WebApp;
  var app = document.getElementById('app');
  var DATA = null;          // { books: [...works], byKey, authors, channels, categories }
  var SAVED = [];           // list of work keys

  // ---------- helpers ----------
  var FA = '۰۱۲۳۴۵۶۷۸۹';
  function fa(n) { return String(n).replace(/\d/g, function (d) { return FA[d]; }); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function norm(s) {
    return String(s || '').toLowerCase()
      .replace(/[يى]/g, 'ی').replace(/ك/g, 'ک').replace(/[ۀة]/g, 'ه').replace(/[أإآ]/g, 'ا')
      .replace(/[ً-ْٰٔ]/g, '')   // اعراب و همزهٔ روی ه
      .replace(/[‌‍‏‎]/g, ' ')    // نیم‌فاصله
      .replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
  }
  function enc(s) { return encodeURIComponent(s); }
  var PALETTE = ['#7A2E2E', '#3B3561', '#2F4A3A', '#5B4A2F', '#1F4E5F', '#4A3B5C', '#6A3A4A', '#34505A', '#5A4632', '#2E3F66'];
  function colorFor(s) {
    var h = 0; s = String(s);
    for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
    return PALETTE[h % PALETTE.length];
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
    logo: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 6.5C10 5 7.5 4.5 4 4.5v13c3.5 0 6 .5 8 2 2-1.5 4.5-2 8-2v-13c-3.5 0-6 .5-8 2z"/><path d="M12 6.5v13"/></svg>'
  };

  // ---------- covers: channel/Excel image → web (ISBN) → default color ----------
  function coverHTML(w, size) {
    var r = w.primary;
    var src = r.cover || '';
    if (!src && r.isbn) {
      var isbn = String(r.isbn).replace(/[^0-9Xx]/g, '');
      if (isbn.length >= 10) src = 'https://covers.openlibrary.org/b/isbn/' + isbn + '-M.jpg?default=false';
    }
    var fb = '<div class="fb" style="background:' + colorFor(w.title) + '"><i></i><b>' + esc(w.title) + '</b><small>' + esc(w.author) + '</small></div>';
    var img = src ? '<img alt="" loading="lazy" referrerpolicy="no-referrer" src="' + esc(src) + '" onload="this.parentNode.classList.add(\'has-img\')" onerror="this.remove()">' : '';
    return '<div class="cover c-' + size + '" role="img" aria-label="جلد ' + esc(w.title) + '">' + fb + img + '</div>';
  }

  // ---------- data ----------
  function buildData(raw) {
    var recs = raw.books || [];
    var works = {}, order = [];
    recs.forEach(function (r, i) {
      if (!r.title) return;
      var key = r.work || (r.isbn ? 'isbn:' + String(r.isbn).replace(/[^0-9Xx]/g, '') : '') ||
        norm(r.title) + '|' + norm(r.author) + '|' + norm(r.translator);
      var w = works[key];
      if (!w) {
        w = works[key] = { key: key, id: 'w' + order.length, title: r.title, author: r.author || '', translator: r.translator || '', copies: [], added: i };
        order.push(w);
      }
      w.copies.push(r);
    });
    order.forEach(function (w) {
      var main = w.copies.filter(function (c) { return c.main; })[0] || w.copies[0];
      w.primary = main;
      w.alts = w.copies.filter(function (c) { return c !== main; });
      w.category = main.category || '';
      w.subjects = main.subjects || [];
      w.hay = norm([w.title, w.author, w.translator, main.publisher, w.category, (w.subjects || []).join(' ')].join(' '));
    });
    var byId = {}; order.forEach(function (w) { byId[w.id] = w; });
    var people = {}, channels = {}, cats = {};
    order.forEach(function (w) {
      if (w.author) (people[w.author] = people[w.author] || []).push(w);
      if (w.translator && w.translator !== w.author) (people[w.translator] = people[w.translator] || []).push(w);
      if (w.category) cats[w.category] = (cats[w.category] || 0) + 1;
      w.copies.forEach(function (c) {
        if (!c.channel) return;
        var ch = channels[c.channel] = channels[c.channel] || { name: c.channel, link: c.channelLink || '', works: [] };
        if (ch.works.indexOf(w) < 0) ch.works.push(w);
      });
    });
    return {
      sample: !!raw.sample, updated: raw.updated || '', works: order, byId: byId,
      people: people, authorsInfo: raw.authors || {}, channels: channels, cats: cats, featured: raw.featured || ''
    };
  }

  // ---------- storage (Telegram CloudStorage → localStorage) ----------
  function loadSaved(cb) {
    try {
      if (tg && tg.CloudStorage && tg.isVersionAtLeast && tg.isVersionAtLeast('6.9')) {
        tg.CloudStorage.getItem('saved', function (err, v) { try { SAVED = JSON.parse(v || '[]'); } catch (e) { SAVED = []; } cb(); });
        return;
      }
    } catch (e) {}
    try { SAVED = JSON.parse(localStorage.getItem('lib_saved') || '[]'); } catch (e) { SAVED = []; }
    cb();
  }
  function storeSaved() {
    var v = JSON.stringify(SAVED);
    try { if (tg && tg.CloudStorage && tg.isVersionAtLeast('6.9')) tg.CloudStorage.setItem('saved', v); } catch (e) {}
    try { localStorage.setItem('lib_saved', v); } catch (e) {}
  }
  function isSaved(w) { return SAVED.indexOf(w.key) >= 0; }
  function toggleSaved(w) {
    var i = SAVED.indexOf(w.key);
    if (i >= 0) SAVED.splice(i, 1); else SAVED.unshift(w.key);
    storeSaved();
    haptic('light');
  }

  // ---------- telegram integration ----------
  function haptic(k) { try { tg && tg.HapticFeedback && tg.HapticFeedback.impactOccurred(k); } catch (e) {} }
  function openLink(url) {
    if (!url) return;
    try {
      if (tg && /^https?:\/\/t\.me\//i.test(url)) { tg.openTelegramLink(url); return; }
      if (tg && tg.openLink) { tg.openLink(url); return; }
    } catch (e) {}
    window.open(url, '_blank', 'noopener');
  }
  function setupTelegram() {
    if (!tg) return;
    try {
      tg.ready(); tg.expand();
      applyScheme();
      tg.onEvent && tg.onEvent('themeChanged', applyScheme);
      tg.BackButton && tg.BackButton.onClick(function () { var b = document.querySelector('[data-back]'); b ? b.click() : go('#/'); });
    } catch (e) {}
  }
  function applyScheme() {
    var dark = tg && tg.colorScheme === 'dark';
    document.documentElement.classList.toggle('dark', !!dark);
    var c = dark ? '#0E1A3D' : '#2346A0';
    try { tg.setHeaderColor(c); tg.setBackgroundColor(c); tg.setBottomBarColor && tg.setBottomBarColor(dark ? '#182654' : '#FFFDF8'); } catch (e) {}
  }
  function go(h) { location.hash = h; }

  // ---------- views ----------
  function shelf(works, size) {
    if (!works.length) return '<div class="empty">کتابی نیست.</div>';
    return '<div class="shelf' + (size === 'sm' ? ' sm' : '') + '">' + works.map(function (w) {
      return '<a href="#/book/' + w.id + '">' + coverHTML(w, size || 'md') +
        '<span class="t">' + esc(w.title) + '</span><span class="a">' + esc(w.author) + '</span></a>';
    }).join('') + '</div>';
  }
  function bookRows(works, person) {
    if (!works.length) return '<div class="empty" style="color:var(--muted)">چیزی پیدا نشد.</div>';
    return works.map(function (w) {
      var role;
      if (person) role = w.author === person ? 'تألیف' : 'ترجمه · اثر ' + w.author;
      else role = [w.author, w.translator ? 'ترجمهٔ ' + w.translator : ''].filter(Boolean).join(' · ');
      return '<a class="row" href="#/book/' + w.id + '">' + coverHTML(w, 'xs') +
        '<div class="grow"><span class="nm" style="font-weight:700;font-size:15px">' + esc(w.title) + '</span>' +
        '<span class="sub">' + esc(role) + '</span>' +
        (w.alts.length ? '<span class="badge">' + fa(w.copies.length) + ' نسخه در کانال‌ها</span>' : '') +
        '</div>' + ICON.chev + '</a>';
    }).join('');
  }
  function notice() {
    return DATA.sample ? '<div class="notice">این نسخهٔ آزمایشی با چند کتاب نمونه است. فهرست کامل کتاب‌ها به‌زودی افزوده می‌شود.</div>' : '';
  }

  function viewHome() {
    var works = DATA.works;
    var cats = Object.keys(DATA.cats);
    var recent = works.slice().sort(function (a, b) { return b.added - a.added; }).slice(0, 12);
    var feat = DATA.byId[DATA.featured] || works.filter(function (w) { return w.primary.link; })[0] || works[0];
    var chans = Object.keys(DATA.channels).map(function (k) { return DATA.channels[k]; })
      .sort(function (a, b) { return b.works.length - a.works.length; }).slice(0, 5);
    var nCh = Object.keys(DATA.channels).length;
    var h = '';
    h += '<header class="top"><div class="brand"><div class="logo">' + ICON.logo + '</div><div><h1>کتابخانه</h1>' +
      '<p>' + fa(works.length) + ' کتاب از ' + fa(nCh) + ' کانال</p></div></div>' +
      '<a class="icon-btn" href="#/saved" aria-label="نشان‌شده‌ها">' + ICON.save + '</a></header>';
    h += notice();
    h += '<form class="search" role="search" onsubmit="return false"><label for="q" class="sr">جستجو در کتابخانه</label>' + ICON.search +
      '<input id="q" type="search" placeholder="عنوان، نویسنده، مترجم یا ناشر…" enterkeyhint="search"></form>';
    if (cats.length) {
      h += '<nav class="chips" aria-label="دسته‌ها"><a class="chip on" href="#/">همه</a>' +
        cats.map(function (c) { return '<a class="chip" href="#/cat/' + enc(c) + '">' + esc(c) + '</a>'; }).join('') + '</nav>';
    }
    h += '<section class="sec"><div class="sec-head"><h2>تازه‌ها</h2><a href="#/all">همه</a></div>' + shelf(recent) + '</section>';
    if (feat) h += '<section class="sec"><div class="sec-head"><h2>پیشنهاد امروز</h2></div>' + featCard(feat) + '</section>';
    if (chans.length) {
      h += '<section class="sec"><div class="sec-head"><h2>مرور بر اساس کانال</h2><a href="#/channels">همهٔ کانال‌ها</a></div>' +
        '<div class="card list">' + chans.map(channelRow).join('') + '</div></section>';
    }
    render(h, 'home');
    var q = document.getElementById('q');
    q.addEventListener('focus', function () { go('#/search'); });
  }
  function featCard(w) {
    var r = w.primary;
    return '<article class="card feat"><div class="feat-top"><a href="#/book/' + w.id + '">' + coverHTML(w, 'xs').replace('c-xs', 'c-xs" style="width:84px;height:120px') + '</a>' +
      '<dl class="kv"><dt>عنوان</dt><dd style="font-weight:700"><a href="#/book/' + w.id + '" style="color:inherit">' + esc(w.title) + '</a></dd>' +
      (w.author ? '<dt>پدیدآور</dt><dd><a href="#/author/' + enc(w.author) + '">' + esc(w.author) + '</a></dd>' : '') +
      (w.translator ? '<dt>مترجم</dt><dd><a href="#/author/' + enc(w.translator) + '">' + esc(w.translator) + '</a></dd>' : '') +
      (r.publisher ? '<dt>ناشر</dt><dd>' + esc(r.publisher) + '</dd>' : '') +
      (r.year ? '<dt>سال</dt><dd>' + esc(fa(r.year)) + '</dd>' : '') +
      (r.channel ? '<dt>کانال</dt><dd>' + esc(r.channel) + '</dd>' : '') +
      '</dl></div>' +
      '<button class="primary in-card" data-open="' + esc(r.link || '') + '"' + (r.link ? '' : ' disabled') + '>' + ICON.tg + (r.link ? 'خواندن در تلگرام' : 'پیوند هنوز ثبت نشده') + '</button></article>';
  }
  function channelRow(ch) {
    return '<a class="row" href="#/channel/' + enc(ch.name) + '"><div class="dot">' + ICON.books + '</div>' +
      '<div class="grow"><span class="nm">' + esc(ch.name) + '</span><span class="sub">' + fa(ch.works.length) + ' کتاب</span></div>' + ICON.chev + '</a>';
  }

  function viewBook(id) {
    var w = DATA.byId[id];
    if (!w) return viewMissing();
    var r = w.primary;
    var meta = [r.publisher, r.year && fa(r.year), r.pages && fa(r.pages) + ' صفحه'].filter(Boolean).join(' · ');
    var saved = isSaved(w);
    var h = '';
    h += '<div class="bar"><a class="icon-btn" href="#/" data-back aria-label="بازگشت">' + ICON.back + '</a><div class="grp">' +
      '<button class="icon-btn" id="share" aria-label="هم‌رسانی">' + ICON.share + '</button>' +
      '<button class="icon-btn' + (saved ? ' on' : '') + '" id="save" aria-label="' + (saved ? 'برداشتن نشان' : 'نشان کردن') + '">' + ICON.save + '</button></div></div>';
    h += '<section class="hero">' + coverHTML(w, 'lg') + '<div style="display:flex;flex-direction:column;gap:6px;align-items:center"><h1>' + esc(w.title) + '</h1>' +
      (w.author ? '<a class="by" href="#/author/' + enc(w.author) + '">' + esc(w.author) + '</a>' : '') +
      (w.translator ? '<a class="by" style="font-size:13px" href="#/author/' + enc(w.translator) + '">ترجمهٔ ' + esc(w.translator) + '</a>' : '') +
      (meta ? '<p>' + esc(meta) + '</p>' : '') + '</div></section>';
    h += '<section class="sec px" style="gap:10px"><button class="primary" data-open="' + esc(r.link || '') + '"' + (r.link ? '' : ' disabled') + '>' + ICON.tg +
      (r.link ? 'خواندن در تلگرام' : 'پیوند هنوز ثبت نشده') + '</button>' +
      '<p class="muted" style="margin:0;text-align:center;font-size:12px">' + esc(['کانال اصلی: ' + (r.channel || '—'), 'PDF', r.size ? fa(r.size) + ' مگابایت' : ''].filter(Boolean).join(' · ')) + '</p></section>';
    if (w.alts.length) {
      h += '<section class="sec"><div class="px" style="display:flex;flex-direction:column;gap:4px"><h2>نسخه‌های دیگر در کانال‌ها</h2>' +
        '<p class="muted" style="margin:0;font-size:13px;line-height:1.7">این کتاب در کانال‌های دیگر هم هست. اگر پیوند اصلی باز نشد، از این‌ها استفاده کنید.</p></div>' +
        '<div class="card list">' + w.alts.map(function (a) {
          var diff = (a.publisher && a.publisher !== r.publisher) || (a.year && String(a.year) !== String(r.year)) || (a.edition && a.edition !== r.edition);
          var m = ['PDF', a.size ? fa(a.size) + ' مگابایت' : '', [a.publisher, a.year && fa(a.year)].filter(Boolean).join('، ')].filter(Boolean).join(' · ');
          return '<div class="row"><div class="dot">' + ICON.file + '</div><div class="grow"><div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap"><span class="nm">' + esc(a.channel || 'کانال') + '</span>' +
            (diff ? '<span class="badge warn">چاپ دیگر</span>' : '') + '</div><span class="sub">' + esc(m) + '</span></div>' +
            '<button class="ghost-btn" data-open="' + esc(a.link || '') + '"' + (a.link ? '' : ' disabled') + ' aria-label="باز کردن نسخهٔ ' + esc(a.channel || '') + '">باز کردن' + ICON.ext + '</button></div>';
        }).join('') + '</div></section>';
    }
    var rec = [['عنوان', w.title], ['پدیدآور', w.author], ['مترجم', w.translator], ['ناشر', r.publisher], ['محل نشر', r.place],
      ['سال نشر', r.year && fa(r.year)], ['نوبت چاپ', r.edition], ['شمار صفحات', r.pages && fa(r.pages) + ' ص.'], ['شابک', r.isbn],
      ['ردهٔ کنگره', r.congress], ['ردهٔ دیویی', r.dewey], ['ش. کتابشناسی ملی', r.nlNumber]].filter(function (x) { return x[1]; });
    h += '<section class="sec"><div class="sec-head"><h2>مشخصات کتاب‌شناختی</h2>' + (r.source ? '<span class="muted" style="font-size:12px">منبع: ' + esc(r.source) + '</span>' : '') + '</div>' +
      '<dl class="card rec">' + rec.map(function (x) { return '<div><dt>' + x[0] + '</dt><dd>' + esc(x[1]) + '</dd></div>'; }).join('') + '</dl>' +
      (w.subjects.length ? '<div class="tags">' + w.subjects.map(function (s) { return '<a class="tag" href="#/search/' + enc(s) + '">' + esc(s) + '</a>'; }).join('') + '</div>' : '') + '</section>';
    var more = (DATA.people[w.author] || []).filter(function (x) { return x !== w; });
    if (more.length) h += '<section class="sec"><div class="sec-head"><h2>از همین نویسنده</h2><a href="#/author/' + enc(w.author) + '">همه</a></div>' + shelf(more, 'sm') + '</section>';
    render(h, null, true);
    document.getElementById('save').onclick = function () { toggleSaved(w); viewBook(id); };
    document.getElementById('share').onclick = function () {
      var bot = (window.LIB_CONFIG && window.LIB_CONFIG.botUsername) || '';
      var url = bot ? 'https://t.me/' + bot + '?startapp=' + w.id : location.href;
      var text = w.title + (w.author ? ' — ' + w.author : '');
      openLink('https://t.me/share/url?url=' + enc(url) + '&text=' + enc(text));
    };
  }

  function viewAuthor(name, filter) {
    var list = DATA.people[name];
    if (!list) return viewMissing();
    filter = filter || 0;
    var info = DATA.authorsInfo[name] || {};
    var own = list.filter(function (w) { return w.author === name; });
    var tr = list.filter(function (w) { return w.translator === name && w.author !== name; });
    var chs = {}; list.forEach(function (w) { w.copies.forEach(function (c) { if (c.channel) chs[c.channel] = 1; }); });
    var shown = filter === 1 ? own : filter === 2 ? tr : list;
    var h = '<div class="bar"><a class="icon-btn" href="#/" data-back aria-label="بازگشت">' + ICON.back + '</a></div>';
    h += '<section class="hero"><div class="avatar" aria-hidden="true">' + esc(name.trim().charAt(0)) + '</div>' +
      '<div style="display:flex;flex-direction:column;gap:4px"><h1 style="font-size:28px">' + esc(name) + '</h1>' +
      (info.bio || info.years ? '<p>' + esc([info.bio, info.years].filter(Boolean).join(' · ')) + '</p>' : '') + '</div>' +
      '<div class="card stats" style="margin:0"><div><b>' + fa(own.length) + '</b><span>تألیف</span></div><div><b>' + fa(tr.length) + '</b><span>ترجمه</span></div><div><b>' + fa(Object.keys(chs).length) + '</b><span>کانال</span></div></div></section>';
    h += '<div class="seg" role="group" aria-label="نوع اثر">' + ['همه', 'تألیف', 'ترجمه'].map(function (l, i) {
      return '<button data-f="' + i + '" aria-pressed="' + (i === filter) + '">' + l + '</button>';
    }).join('') + '</div>';
    h += '<section class="sec"><div class="sec-head"><h2>کتاب‌ها در کتابخانه</h2></div><div class="card list">' + bookRows(shown, name) + '</div></section>';
    render(h, null, true);
    [].forEach.call(document.querySelectorAll('.seg button'), function (b) {
      b.onclick = function () { haptic('light'); viewAuthor(name, +b.getAttribute('data-f')); };
    });
  }

  function viewSearch(initial) {
    var h = '<form class="search" role="search" onsubmit="return false" style="margin-top:4px"><label for="q" class="sr">جستجو در کتابخانه</label>' + ICON.search +
      '<input id="q" type="search" placeholder="عنوان، نویسنده، مترجم یا ناشر…" enterkeyhint="search" value="' + esc(initial || '') + '"></form>' +
      '<section class="sec"><div class="card list" id="res"></div></section>';
    render(h, 'search');
    var q = document.getElementById('q'), res = document.getElementById('res');
    function run() {
      var t = norm(q.value);
      if (!t) { res.innerHTML = '<div class="empty" style="color:var(--muted)">نام کتاب، نویسنده، مترجم یا ناشر را بنویسید.</div>'; return; }
      var parts = t.split(' ');
      var hits = DATA.works.filter(function (w) { return parts.every(function (p) { return w.hay.indexOf(p) >= 0; }); });
      var people = Object.keys(DATA.people).filter(function (p) { return norm(p).indexOf(t) >= 0; }).slice(0, 5);
      res.innerHTML = people.map(function (p) {
        return '<a class="row" href="#/author/' + enc(p) + '"><div class="dot" style="font-family:var(--serif);font-weight:700;color:var(--accent)">' + esc(p.charAt(0)) + '</div><div class="grow"><span class="nm">' + esc(p) + '</span><span class="sub">' + fa(DATA.people[p].length) + ' کتاب</span></div>' + ICON.chev + '</a>';
      }).join('') + bookRows(hits);
    }
    q.addEventListener('input', run);
    run();
    setTimeout(function () { q.focus(); }, 50);
  }

  function viewList(title, works, tab) {
    var h = '<div class="bar"><a class="icon-btn" href="#/" data-back aria-label="بازگشت">' + ICON.back + '</a></div>' +
      '<section class="sec"><div class="sec-head"><h2 style="font-size:22px">' + esc(title) + '</h2><span class="muted" style="font-size:13px">' + fa(works.length) + ' کتاب</span></div>' +
      '<div class="card list">' + bookRows(works) + '</div></section>';
    render(h, tab || null, true);
  }
  function viewChannel(name) {
    var ch = DATA.channels[name]; if (!ch) return viewMissing();
    viewList(name, ch.works);
    if (ch.link) {
      var b = document.createElement('div'); b.className = 'px';
      b.innerHTML = '<button class="primary" data-open="' + esc(ch.link) + '">' + ICON.tg + 'رفتن به کانال</button>';
      app.insertBefore(b, app.children[1]);
    }
  }
  function viewChannels() {
    var all = Object.keys(DATA.channels).map(function (k) { return DATA.channels[k]; }).sort(function (a, b) { return b.works.length - a.works.length; });
    render('<div class="bar"><a class="icon-btn" href="#/" data-back aria-label="بازگشت">' + ICON.back + '</a></div>' +
      '<section class="sec"><div class="sec-head"><h2 style="font-size:22px">کانال‌ها</h2></div><div class="card list">' + all.map(channelRow).join('') + '</div></section>', null, true);
  }
  function viewCategories() {
    var cats = Object.keys(DATA.cats);
    render('<section class="sec"><div class="sec-head"><h2 style="font-size:22px">دسته‌ها</h2></div>' +
      (cats.length ? '<div class="grid">' + cats.map(function (c) { return '<a href="#/cat/' + enc(c) + '"><b>' + esc(c) + '</b><span>' + fa(DATA.cats[c]) + ' کتاب</span></a>'; }).join('') + '</div>' : '<div class="empty">هنوز دسته‌ای ثبت نشده.</div>') +
      '</section><section class="sec"><div class="sec-head"><h2>کانال‌ها</h2><a href="#/channels">همه</a></div><div class="card list">' +
      Object.keys(DATA.channels).slice(0, 6).map(function (k) { return channelRow(DATA.channels[k]); }).join('') + '</div></section>', 'categories');
  }
  function viewSaved() {
    var works = SAVED.map(function (k) { return DATA.works.filter(function (w) { return w.key === k; })[0]; }).filter(Boolean);
    render('<section class="sec"><div class="sec-head"><h2 style="font-size:22px">نشان‌شده‌ها</h2></div>' +
      (works.length ? '<div class="card list">' + bookRows(works) + '</div>' : '<div class="empty">هنوز کتابی نشان نکرده‌اید. در صفحهٔ هر کتاب، دکمهٔ نشان را بزنید.</div>') + '</section>', 'saved');
  }
  function viewMissing() { render('<div class="empty">این صفحه پیدا نشد. <a href="#/" style="color:var(--gold)">بازگشت به خانه</a></div>', null, true); }

  function render(html, tab, sub) {
    app.innerHTML = html;
    window.scrollTo(0, 0);
    [].forEach.call(document.querySelectorAll('.tabbar a'), function (a) {
      var on = a.getAttribute('data-tab') === tab;
      a.classList.toggle('on', on);
      if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
    try { if (tg && tg.BackButton) { sub ? tg.BackButton.show() : tg.BackButton.hide(); } } catch (e) {}
  }

  // open buttons (delegated)
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
    var h = decodeURIComponent((location.hash || '#/').slice(1));
    var p = h.split('/').filter(Boolean);
    if (!p.length) return viewHome();
    switch (p[0]) {
      case 'book': return viewBook(p[1]);
      case 'author': return viewAuthor(p.slice(1).join('/'));
      case 'channel': return viewChannel(p.slice(1).join('/'));
      case 'channels': return viewChannels();
      case 'cat': return viewList(p.slice(1).join('/'), DATA.works.filter(function (w) { return w.category === p.slice(1).join('/'); }), 'categories');
      case 'categories': return viewCategories();
      case 'search': return viewSearch(p.slice(1).join('/'));
      case 'saved': return viewSaved();
      case 'all': return viewList('همهٔ کتاب‌ها', DATA.works);
      default: return viewMissing();
    }
  }

  // ---------- boot ----------
  setupTelegram();
  fetch('data/books.json', { cache: 'no-cache' }).then(function (r) { return r.json(); }).then(function (raw) {
    DATA = buildData(raw);
    loadSaved(function () {
      var start = tg && tg.initDataUnsafe && tg.initDataUnsafe.start_param;
      if (start && DATA.byId[start] && !location.hash) history.replaceState(null, '', '#/book/' + start);
      window.addEventListener('hashchange', route);
      route();
    });
  }).catch(function () {
    app.innerHTML = '<div class="empty">بارگذاری فهرست کتاب‌ها ممکن نشد. لطفاً دوباره امتحان کنید.</div>';
  });
})();
