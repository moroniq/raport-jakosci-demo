"""Raport poranny (markdown) -> strony w stylu Pomelo (pomelo-raport.css).

Użycie:  python md2strona.py 2026-11-08
Czyta discovery/raport-poranny/<data>.md, zapisuje prototypes/raport-strona/<data>/*.html.
Sekcje ## trafiają do zakładek wg nazw; tabele z pustym nagłówkiem (Dowód/Partia/...) stają się kartą problemu.
"""
import html, os, re, sys

TU = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(TU))
DNI = ['pon', 'wt', 'śr', 'czw', 'pt', 'sob', 'ndz']

ZAKLADKI = [  # plik, nazwa, prefiksy nagłówków ##
    ('index.html', 'Podsumowanie', ['Podsumowanie', 'KPI']),
    ('dni.html', 'Ostatnie 7 dni', ['Przedwczoraj', 'Wczoraj', 'Nowe sygnały']),
    ('dzien-noc.html', 'Dzień i noc', ['Zmiany kuchni']),
    ('tydzien.html', 'Tydzień', ['Tydzień', 'Bieżący tydzień']),
    ('klienci.html', 'Klienci', ['Klienci']),
    ('pdca.html', 'PDCA', ['Propozycje do PDCA', 'Dla dietetyki', 'Uzupełnienie']),
    ('dodatki.html', 'Dodatki', ['Dodatkowo']),
]
STATUS = {'🟢': ('dobrze', 'w normie'), '🟡': ('uwaga', 'uwaga'), '🔴': ('zle', 'poza celem')}


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<i>\1</i>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'„([^”]{1,160})”', r'<span class="cytat">„\1”</span>', t)
    for e, (k, n) in STATUS.items():
        t = t.replace(e, f'<span class="st {k}">{n}</span>')
    t = t.replace('⚠', '<span class="st zle">uwaga</span>')
    return t


LICZ = r'(\d+(?:,\d+)?)'


def _chip(p, pc):
    a, b = float(p.replace(',', '.')), float(pc.replace(',', '.'))
    k = 'zle' if a >= b + 0.5 else ('dobrze' if a <= b else 'uwaga')
    return f'<span class="st {k}">{p}%</span> <span class="cel">({pc}%)</span>'


def _sr(x):
    return f'{float(x.replace(",", ".")):.2f}'.replace('.', ',')


def komorka_dn(c):
    """Komórki z tabel dzień/noc -> czytelny układ: % 1–2 jako kolorowy znacznik, reszta drobnym drukiem w drugiej linii."""
    c = c.replace('**', '')
    m = re.fullmatch(LICZ + r'% \(' + LICZ + r'%\) · śr\. ' + LICZ + r' · wyk\. ' + LICZ + r'/100 · n=(\d+)', c.strip())
    if m:
        p, pc, sr, wy, n = m.groups()
        return f'<td class="num">{_chip(p, pc)}<br><span class="cel">śr. {_sr(sr)} · wyk. {wy}</span></td>'
    m = re.fullmatch(LICZ + r' · ' + LICZ + r'% · ' + LICZ + r' \(' + LICZ + r' · ' + LICZ + r'% · ' + LICZ + r'\), n=([\d ]+)', c.strip())
    if m:
        sr, p, wy, src, pc, wyc, n = m.groups()
        return f'<td class="num">{_chip(p, pc)}<br><span class="cel">śr. {_sr(sr)} ({_sr(src)}) · wyk. {wy} ({wyc})</span></td>'
    return None


def tabela(wiersze, tytul=None):
    kom = [[c.strip() for c in w.strip().strip('|').split('|')] for w in wiersze]
    sep = lambda k: all(re.fullmatch(r':?-{2,}:?', c) for c in k)
    kom = [k for k in kom if not sep(k)]
    nag, reszta = kom[0], kom[1:]
    if not any(nag):  # karta problemu: | **Dowód** | ... |
        dl = ''.join(f'<dt>{inline(k[0].strip("*"))}</dt><dd>{inline(" | ".join(k[1:]))}</dd>' for k in reszta if k)
        num, tyt = '', tytul or ''
        m = re.match(r'([①-⑳])\s*(.*)', tyt)
        if m:
            num, tyt = m.groups()
        return f'<article class="problem"><header><span class="nr">{num}</span><h3>{inline(tyt)}</h3></header><dl>{dl}</dl></article>'
    h = '<tr>' + ''.join(f'<th>{inline(c)}</th>' for c in nag) + '</tr>'
    rola = [('p12' if '1–2' in c else 'sr' if c.lower().startswith('średnia') else 'partia' if c.lower().startswith('partia') else 'danie' if j == 0 and c.lower().startswith('danie') else '') for j, c in enumerate(nag)]
    for k in reszta:
        h += '<tr>' + ''.join(komorka_dn(c) or komorka_danie(c, rola[j] if j < len(rola) else '') for j, c in enumerate(k)) + '</tr>'
    return f'<table class="tab">{h}</table>'


OSOBA = re.compile(r'(?<![\w>])([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+ [A-ZĄĆĘŁŃÓŚŹŻ][a-z]?\.)(?!\w)')


def komorka_danie(c, rola):
    """Tabela dań jak na dawnych stronach „Wczoraj”: kolorowy znacznik % ocen 1–2 i średniej, nazwa dania pogrubiona, osoby wyróżnione."""
    t = c.strip()
    if rola == 'p12':
        m = re.match(r'\*{0,2}(\d+(?:,\d+)?)%\*{0,2}\s*\((\d+(?:,\d+)?)%?([^)]*)\)(.*)$', t)
        if m:
            p, pc, reszta, ogon = m.groups()
            n = re.search(r'n=([\d ]+)', reszta)
            return f'<td class="num">{_chip(p, pc)}' + (f'<br><span class="cel">n={n.group(1)} w cyklach</span>' if n else '') + (f' {inline(ogon)}' if ogon.strip() else '') + '</td>'
        m = re.match(r'\*{0,2}(\d+(?:,\d+)?)%\*{0,2}\s*\((nowe|nowość)\)', t)
        if m:
            k = 'zle' if float(m.group(1).replace(',', '.')) >= 4 else 'uwaga'
            return f'<td class="num"><span class="st {k}">{m.group(1)}%</span> <span class="cel">(nowe)</span></td>'
    if rola == 'sr':
        m = re.match(r'\*{0,2}(\d,\d+)\*{0,2}\s*\((\d,\d+|nowe)\)(?:\s*·\s*([−-]?\d,\d+))?(.*)$', t)
        if m:
            sr, src, vs, ogon = m.groups()
            if src == 'nowe':
                k = 'uwaga'
            else:
                r = float(sr.replace(',', '.')) - float(src.replace(',', '.'))
                k = 'zle' if r <= -0.15 else ('uwaga' if r < 0 else 'dobrze')
            return f'<td class="num"><span class="st {k}">{sr}</span> <span class="cel">({src})</span>' + (f'<br><span class="cel">{vs} vs dzień</span>' if vs else '') + (f' {inline(ogon)}' if ogon.strip() else '') + '</td>'
    if rola == 'danie':
        return f'<td><b>{inline(t.replace("**", ""))}</b></td>'
    if rola == 'partia':
        x = inline(t.replace('**', ''))
        return '<td>' + OSOBA.sub(r'<span class="osoba">\1</span>', x) + '</td>'
    return f'<td>{inline(c)}</td>'


def kafelki_dnia(tekst):
    """Akapit „**Dzień:** … W tym samym wieku …: 3,66% i 4,56 wobec 2,96% i 4,60.” -> kafelki jak na dawnych stronach."""
    t = tekst.replace('**', '')
    n = re.search(r'([\d ]*\d) ocen', t)
    m = re.search(r'tym samym wieku[^:]*:\s*(\d+,\d+)% i (\d,\d+) wobec (\d+,\d+)% i (\d,\d+)', t)
    if m:
        p, sr, pc, src = m.groups(); opis = 'w tym samym wieku ocen, te same dni w cyklach'
    else:
        m2 = re.search(r'średnia (\d,\d+), (\d+,\d+)% ocen 1–2', t); m3 = re.search(r'średnio (\d+,\d+)% i (\d,\d+)', t)
        if not (m2 and m3):
            return None
        p, sr, pc, src = m2.group(2), m2.group(1), m3.group(1), m3.group(2); opis = 'te same dni w cyklach'
    a, b = float(p.replace(',', '.')), float(pc.replace(',', '.'))
    k1 = 'zle' if a >= b + 0.5 else ('dobrze' if a <= b else 'uwaga')
    d = float(sr.replace(',', '.')) - float(src.replace(',', '.'))
    k2 = 'zle' if d <= -0.05 else ('dobrze' if d >= 0 else 'uwaga')
    nazwy = {'zle': 'poza normą', 'uwaga': 'uwaga', 'dobrze': 'w normie'}
    splyw = 'spływają' in t or 'święto' in t
    werdykt = re.search(r'\*\*(To [^*]+)\*\*', tekst)
    return ('<div class="kafelki">'
            f'<div class="kafel {k1}"><div class="co">Oceny 1–2 · w tym samym wieku</div><div class="liczba">{p}%</div><div class="por">{opis}: {pc}%</div><div class="pasek-celu" data-wartosc="{a}" data-max="6" data-cel="3"><i></i><b></b></div><span class="st {k1}">{nazwy[k1]}</span>' + (' <span class="st szary">oceny spływają</span>' if splyw else '') + '</div>'
            f'<div class="kafel {k2}"><div class="co">Średnia</div><div class="liczba">{sr}</div><div class="por">w cyklach {src} · cel 4,63</div><span class="st {k2}">{nazwy[k2]}</span></div>'
            f'<div class="kafel"><div class="co">Ocen</div><div class="liczba">{n.group(1).strip() if n else "—"}</div><div class="por">{inline(werdykt.group(1)) if werdykt else ""}</div></div>'
            '</div>')


def blok(linie):
    """Treść jednej sekcji ## -> HTML."""
    out, i, nr_h3 = [], 0, None
    akap = []

    def zrzut():
        if akap:
            t = ' '.join(akap)
            if t.startswith('**Dzień'):
                k = kafelki_dnia(t)
                if k:
                    out.append(k)
            out.append('<p>' + inline(t) + '</p>')
            akap.clear()
    while i < len(linie):
        l = linie[i].rstrip()
        if l.startswith('### '):
            zrzut()
            nr_h3 = l[4:].strip()
            if i + 1 < len(linie) and linie[i + 1].lstrip().startswith('|') and re.match(r'\|\s*\|\s*\|', linie[i + 1].strip()):
                i += 1
                continue
            out.append(f'<h3 class="pod-h">{inline(nr_h3)}</h3>')
            nr_h3 = None
        elif l.lstrip().startswith('|'):
            zrzut()
            t = []
            while i < len(linie) and linie[i].lstrip().startswith('|'):
                t.append(linie[i]); i += 1
            out.append(tabela(t, nr_h3)); nr_h3 = None
            continue
        elif re.match(r'\s*([-*]|\d+\.)\s+', l):
            zrzut()
            num = bool(re.match(r'\s*\d+\.', l))
            items = []
            while i < len(linie) and (re.match(r'\s*([-*]|\d+\.)\s+', linie[i]) or (linie[i].startswith('  ') and linie[i].strip())):
                s = linie[i]
                if re.match(r'\s*([-*]|\d+\.)\s+', s):
                    ind = len(s) - len(s.lstrip())
                    items.append([ind, re.sub(r'^\s*([-*]|\d+\.)\s+', '', s)])
                else:
                    items[-1][1] += ' ' + s.strip()
                i += 1
            if out and 'Najbliższe podania' in out[-1]:
                out[-1] = '<h3 class="pod-h">Najbliższe podania <small style="font-weight:400;color:#777">działania do przodu</small></h3>'
                karty = ''
                for ind, t in items:
                    m = re.match(r'\*\*(.+?)\*\*:?\s*(.*)$', t)
                    if m and len(m.group(1)) < 90:
                        tyt, reszta = m.group(1).rstrip(':'), m.group(2)
                    elif ':' in t[:70]:
                        tyt, reszta = t.split(':', 1)
                    else:
                        tyt, reszta = '', t
                    pilne = re.search(r'dziś|jutro|pilne', tyt + reszta[:60], re.I)
                    karty += '<div class="karta">' + (f'<span class="st {"zle" if pilne else "szary"}">{inline(tyt)}</span>' if tyt else '') + f'<p>{inline(reszta)}</p></div>'
                out.append(f'<div class="kafelki">{karty}</div>')
                continue
            tag = 'ol' if num else 'ul'
            out.append(f'<div class="karta podsum"><{tag} style="margin:0;padding-left:20px">' + ''.join(
                f'<li style="margin:4px 0{";margin-left:18px" if ind else ""}">{inline(t)}</li>' for ind, t in items) + f'</{tag}></div>')
            continue
        elif l.strip() in ('', '---'):
            zrzut()
        else:
            akap.append(l.strip())
        i += 1
    zrzut()
    return '\n'.join(out)


def wersje_dni(data):
    """Dla raportu z dnia `data`: ostatnie 7 dni jedzenia i wszystkie wersje ich sekcji z raportów do `data` włącznie."""
    import datetime as dt
    r = dt.date.fromisoformat(data)
    dni = [r - dt.timedelta(days=k) for k in range(7, 0, -1)]
    wer = {d: [] for d in dni}
    for k in range(0, 10):
        rd = r - dt.timedelta(days=k)
        f = os.path.join(PROJ, 'discovery', 'raport-poranny', f'{rd.isoformat()}.md')
        if not os.path.exists(f):
            continue
        akt = None
        for l in open(f, encoding='utf-8').read().splitlines():
            if l.startswith('## '):
                nag = l[3:].strip()
                akt = None
                if nag.startswith(('Przedwczoraj', 'Wczoraj', 'Nowe sygnały')):
                    akt = [rd, nag, []]
                    for dd, mm in re.findall(r'(\d{1,2})\.(\d{1,2})(?!\d)', nag.split('(')[0]):
                        try:
                            d = dt.date(rd.year if int(mm) <= rd.month else rd.year - 1, int(mm), int(dd))
                        except ValueError:
                            continue
                        if d in wer:
                            wer[d].append(akt)
            elif akt is not None:
                akt[2].append(l)
    for d in wer:
        wer[d].sort(key=lambda v: (v[0], v[1].startswith('Przedwczoraj')), reverse=True)
    return dni, wer


def strona_dni(data, wybrany=None):
    """Jedna strona = jeden dzień (cała zakładka w jednym pliku przekraczała limit serwera podglądu ~127 KB)."""
    dni, wer = wersje_dni(data)
    nawig, panele = '', ''
    wybrany = wybrany or dni[-2].isoformat()
    for d in dni:
        iso = d.isoformat()
        et = f'{DNI[d.weekday()]} {d.day}.{d.month}'
        v = wer[d]
        nawig += f'<a class="dzien-tab{" on" if iso == wybrany else ""}" href="dzien-{iso}.html">{et}<small>{len(v)} wers.</small></a>'
        if iso != wybrany:
            continue
        glowne = [x for x in v if not x[1].startswith('Nowe sygnały')]
        nowe = [x for x in v if x[1].startswith('Nowe sygnały') and (not glowne or x[0] > glowne[0][0])]
        tresc = ''
        for rdn, nagn, linn in nowe:
            tresc += f'<div class="karta" style="border-left:6px solid #FF7800"><p><b>Nowe sygnały – raport z {rdn.day}.{rdn.month}</b></p>{blok(linn)}</div>'
        if not glowne:
            tresc += '<p class="pod">Brak sekcji o tym dniu w raportach (raport wstrzymany albo dzień jeszcze nieomawiany).</p>'
        else:
            rd, nag, lin = glowne[0]
            tresc += f'<p class="zrodla">Wersja z raportu z {rd.day}.{rd.month} – sekcja „{inline(nag)}”.</p>' + blok(lin)
            for rd2, nag2, lin2 in glowne[1:]:
                tresc += f'<details class="karta"><summary>Wcześniejsza wersja: raport z {rd2.day}.{rd2.month} – „{inline(nag2)}”</summary>{blok(lin2)}</details>'
        panele += f'<section class="dzien" id="d-{iso}" style="display:block"><h2>{DNI[d.weekday()]} {d.day}.{d.month}.{d.year}</h2>{tresc}</section>'
    js = ''
    css = '.dni-nav{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 18px}.dzien-tab{display:flex;flex-direction:column;align-items:center;padding:8px 14px;border-radius:10px;background:#f1f3ee;color:#2F4F3A;text-decoration:none;font-weight:600}.dzien-tab small{font-weight:400;font-size:11px;color:#777}.dzien-tab.on{background:#2F4F3A;color:#fff}.dzien-tab.on small{color:#ddd}details.karta{margin:14px 0}details summary{cursor:pointer;font-weight:600}'
    return f'<style>{css}</style><p class="pod">Każdy dzień jedzenia z ostatnich 7 dni osobno. Pokazana jest najnowsza wersja z raportów porannych; gdy dochodzą sygnały (oceny, BOK), kolejny raport ją poprawia, a starsze wersje są niżej.</p><nav class="dni-nav">{nawig}</nav>{panele}{js}'


def main(data):
    zrodlo = os.path.join(PROJ, 'discovery', 'raport-poranny', f'{data}.md')
    tekst = open(zrodlo, encoding='utf-8').read().splitlines()
    tytul = tekst[0].lstrip('# ').strip()
    sekcje, intro, akt = [], [], None
    for l in tekst[1:]:
        if l.startswith('## '):
            akt = [l[3:].strip(), []]; sekcje.append(akt)
        elif akt:
            akt[1].append(l)
        else:
            intro.append(l)
    import datetime as dt
    d = dt.date.fromisoformat(data)
    etykieta = f'{DNI[d.weekday()]} {d.day}.{d.month}.{d.year}'
    folder = os.path.join(TU, data); os.makedirs(folder, exist_ok=True)
    przydzial = {p: [] for p, _, _ in ZAKLADKI}
    for nag, tresc in sekcje:
        cel = next((p for p, _, pre in ZAKLADKI if any(nag.startswith(x) for x in pre)), 'dodatki.html')
        przydzial[cel].append((nag, tresc))
    zrodla = inline(' '.join(x.strip() for x in intro if x.strip() and x.strip() != '---').strip('*'))
    for n, (plik, nazwa, _) in enumerate(ZAKLADKI):
        nav = ''.join(f'<a{" class=\"on\"" if p == plik else ""} href="{p}">{nz}</a>' for p, nz, _ in ZAKLADKI)
        body = ''
        for k, (nag, tresc) in enumerate(przydzial[plik]):
            body += f'<h2><span class="nr">{n + 1}{"abcdef"[k] if len(przydzial[plik]) > 1 else ""}</span>{inline(nag)}</h2>\n'
            b = blok(tresc)
            if nag.startswith('Podsumowanie'):
                b = f'<div class="podsum karta">{b}</div>'
            body += b + '\n'
        if plik == 'dni.html':
            body = strona_dni(data)
            dni_lista, _ = wersje_dni(data)
            dodatkowe = [(f'dzien-{x.isoformat()}.html', strona_dni(data, x.isoformat())) for x in dni_lista]
        else:
            dodatkowe = []
        if not body:
            body = '<p class="pod">W tym raporcie nie ma tej sekcji.</p>'
        h1 = inline(tytul) if plik == 'index.html' else f'{nazwa} <span class="podkr">w raporcie z {etykieta}</span>'
        strona = f'''<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{nazwa} – raport {d.day}.{d.month}</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Rubik:wght@500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../pomelo-raport.css"><script src="../pomelo-raport.js?v=3" defer></script>
<style>.strona p{{margin:8px 0}} .pod-h{{font-family:Rubik;font-size:17px;margin:22px 0 8px}} .tab td{{vertical-align:top}} .problem dd{{margin-bottom:8px}}</style>
</head><body>
<div class="pasek"><div class="logo">pomelo <span>·</span> raport jakości</div><nav>{nav}</nav><div class="data">{etykieta}</div></div>
<main class="strona">
<h1>{h1}</h1>
<p class="zrodla">{zrodla if plik == 'index.html' else 'Raport poranny ' + etykieta + ' · pełne źródła na stronie Podsumowanie'}</p>
{body}
</main></body></html>
'''
        open(os.path.join(folder, plik), 'w', encoding='utf-8').write(strona)
        for plik2, body2 in dodatkowe:   # strony pojedynczych dni – ta sama nawigacja górna, zakładka „Ostatnie 7 dni” podświetlona
            open(os.path.join(folder, plik2), 'w', encoding='utf-8').write(strona.replace(body, body2) if body else strona)
    print('zapisano', folder)


if __name__ == '__main__':
    main(sys.argv[1])
