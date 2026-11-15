/* Pomelo – efekty raportu: wejście sekcji, liczniki w kafelkach, pasek względem celu. Bez ruchu przy prefers-reduced-motion. */
(function(){
  var bezRuchu = (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) || /[?&]statyczny/.test(location.search);
  var d = document.documentElement;
  if (!bezRuchu) d.classList.add('fx');
  function liczba(el){
    var t = el.textContent.trim(), m = t.match(/^([+\-]?)(\d+(?:,\d+)?)(.*)$/);
    if (!m) return;
    var cel = parseFloat(m[2].replace(',', '.')), dec = (m[2].split(',')[1] || '').length;
    if (bezRuchu) return;
    var start = null, czas = 900;
    function krok(ts){ if (!start) start = ts; var p = Math.min(1, (ts - start) / czas), e = 1 - Math.pow(1 - p, 3);
      el.textContent = m[1] + (cel * e).toFixed(dec).replace('.', ',') + m[3]; if (p < 1) requestAnimationFrame(krok); }
    requestAnimationFrame(krok);
  }
  function pasek(k){
    var p = k.querySelector('.pasek-celu'); if (!p) return;
    var w = parseFloat(p.dataset.wartosc), mx = parseFloat(p.dataset.max), c = parseFloat(p.dataset.cel);
    var i = p.querySelector('i'), b = p.querySelector('b');
    if (b) b.style.left = Math.min(100, c / mx * 100) + '%';
    requestAnimationFrame(function(){ i.style.width = Math.min(100, w / mx * 100) + '%'; });
  }
  document.addEventListener('DOMContentLoaded', function(){
    var cele = document.querySelectorAll('.strona > h2, .strona > .karta, .kafelki, .problem, table.tab, .pod, .zrodla');
    cele.forEach(function(el){ el.classList.add('wejdz'); });
    var obs = 'IntersectionObserver' in window ? new IntersectionObserver(function(wpisy){
      wpisy.forEach(function(w){ if (!w.isIntersecting) return; var el = w.target; el.classList.add('widac'); obs.unobserve(el);
        if (el.classList.contains('kafelki')) el.querySelectorAll('.kafel').forEach(function(k, n){ setTimeout(function(){ liczba(k.querySelector('.liczba')); pasek(k); }, n * 120); });
      });
    }, { threshold: 0, rootMargin: '0px 0px -8% 0px' }) : null;   // threshold 0: długie tabele (wyższe niż ekran) też się pokazują
    cele.forEach(function(el, n){ if (obs && !bezRuchu) { el.style.transitionDelay = Math.min(n, 4) * 60 + 'ms'; obs.observe(el); } else { el.classList.add('widac'); if (el.classList.contains('kafelki')) el.querySelectorAll('.kafel').forEach(pasek); } });
    setTimeout(function(){ document.body.classList.add('gotowe'); }, 50);
    // zabezpieczenie: po 1,2 s wszystko jest widoczne, nawet gdy przeglądarka nie zgłosi wejścia elementu na ekran
    setTimeout(function(){ cele.forEach(function(el){ if (!el.classList.contains('widac')) { el.classList.add('widac'); if (el.classList.contains('kafelki')) el.querySelectorAll('.kafel').forEach(pasek); } }); }, 1200);
  });
})();
