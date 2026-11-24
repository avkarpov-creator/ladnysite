// Общий скрипт страниц услуг. Логика та же, что на главной (там пока inline).
// Яндекс.Метрика загружается только после согласия посетителя (152-ФЗ).
(function(){
  var ID = 113935228, KEY = 'ls-consent', TTL = 365 * 24 * 3600 * 1000;
  var box = document.getElementById('consent'), loaded = false;

  function read(){
    try { var c = JSON.parse(localStorage.getItem(KEY)); return c && Date.now() - c.t < TTL ? c.v : null; }
    catch (e) { return null; }
  }
  function save(v){ try { localStorage.setItem(KEY, JSON.stringify({ v: v, t: Date.now() })); } catch (e) {} }

  function loadMetrika(){
    if (loaded) return; loaded = true;
    (function(m,e,t,r,i,k,a){
      m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
      m[i].l=1*new Date();
      for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
      k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
    })(window, document, 'script', 'https://mc.yandex.ru/metrika/tag.js?id=' + ID, 'ym');
    ym(ID, 'init', {ssr:true, webvisor:true, clickmap:true, referrer:document.referrer, url:location.href, accurateTrackBounce:true, trackLinks:true});
  }

  window.lsGoal = function(g){ if (loaded) ym(ID, 'reachGoal', g); };
  document.addEventListener('click', function(e){
    var a = e.target.closest && e.target.closest('a[href]'); if (!a) return;
    var h = a.getAttribute('href');
    if (h.indexOf('t.me/') > -1) lsGoal('tg_click');
    else if (h.indexOf('tel:') === 0) lsGoal('phone_click');
    else if (h.indexOf('mailto:') === 0) lsGoal('email_click');
  });

  if (box) {
    box.addEventListener('click', function(e){
      var v = e.target.getAttribute('data-consent'); if (!v) return;
      var was = read();
      save(v); box.classList.remove('show');
      if (v === 'all') loadMetrika();
      else if (was === 'all') location.reload();
    });
    var open = document.getElementById('consent-open');
    if (open) open.addEventListener('click', function(){ box.classList.add('show'); });
    var c = read();
    if (c === 'all') loadMetrika();
    else if (!c) setTimeout(function(){ box.classList.add('show'); }, 1200);
  }
})();

(function(){
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var header = document.getElementById('top');
  var onScroll = function(){ header.classList.toggle('scrolled', scrollY > 10); };
  addEventListener('scroll', onScroll, {passive:true}); onScroll();

  var groups = new Map();
  document.querySelectorAll('[data-r]').forEach(function(el){
    var p = el.parentElement, i = groups.get(p) || 0;
    el.style.setProperty('--d', Math.min(i, 5) * 0.09 + 's');
    groups.set(p, i + 1);
  });

  if (!('IntersectionObserver' in window) || reduce) {
    document.querySelectorAll('[data-r]').forEach(function(el){ el.classList.add('in'); });
    return;
  }
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if (!e.isIntersecting) return;
      e.target.classList.add('in');
      io.unobserve(e.target);
    });
  }, {threshold:.15, rootMargin:'0px 0px -40px 0px'});
  document.querySelectorAll('[data-r]').forEach(function(el){ io.observe(el); });
})();
