"""Buduje publiczne DEMO raportu porannego (fikcyjne dane) do folderu site/ dla Netlify.

Użycie:  python zbuduj_demo.py [ścieżka do md2strona.py]

1. Kopiuje generator stron (md2strona.py + arkusz stylów + skrypt efektów) do tymczasowego folderu _build/,
   razem z fikcyjnymi raportami z dane-testowe/*.md, i generuje strony tak samo jak dla prawdziwego raportu.
2. Składa site/ z najnowszego dnia: strony + style i skrypt obok, baner „DEMO – dane fikcyjne”, stopka.
3. Sprawdza, że w site/ nie ma odwołań do plików spoza site/, e-maili, numerów telefonów ani linków do prototypu spotkania.
   Przy błędzie site/ nie zostaje podmieniony.
Generator domyślnie pochodzi z ../raport-strona (wersja Olgi); w repozytorium jest jego kopia w generator/.
"""
import html, importlib.util, os, re, shutil, sys

TU = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(TU, 'generator')
BUILD = os.path.join(TU, '_build')
SITE = os.path.join(TU, 'site')
BANER = ('<div role="note" style="margin:12px 0 18px;padding:12px 16px;border-radius:10px;background:#FFF4E5;'
         'border-left:6px solid #FF7800;font:600 14px Montserrat,sans-serif;color:#5A3200">'
         'WERSJA DEMONSTRACYJNA – wszystkie dania, liczby, komentarze i osoby są fikcyjne. '
         'Prawdziwy raport jest dostępny tylko dla zespołu.</div>')
STOPKA = ('<footer style="max-width:1100px;margin:32px auto 24px;padding:12px 16px;border-top:1px solid #ddd;'
          'font:13px Montserrat,sans-serif;color:#595959">Demo prototypu „Raport jakości” – kurs AI Product Heroes. Dane fikcyjne.</footer>')
TELEFON = re.compile(r'(?<![\d.,])(?:\+?48[ -]?)?\d{3}[ -]\d{3}[ -]\d{3}(?![\d.,])')
EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}')


def odswiez_generator():
    """Gdy obok jest folder Olgi raport-strona – bierze stamtąd aktualny generator do generator/."""
    zrodlo = os.path.join(os.path.dirname(TU), 'raport-strona')
    if os.path.isfile(os.path.join(zrodlo, 'md2strona.py')):
        os.makedirs(GEN, exist_ok=True)
        for f in ('md2strona.py', 'pomelo-raport.css', 'pomelo-raport.js'):
            shutil.copy2(os.path.join(zrodlo, f), os.path.join(GEN, f))


def generuj():
    shutil.rmtree(BUILD, ignore_errors=True)
    strona = os.path.join(BUILD, 'prototypes', 'raport-strona')
    raporty = os.path.join(BUILD, 'discovery', 'raport-poranny')
    os.makedirs(strona); os.makedirs(raporty)
    for f in os.listdir(GEN):
        shutil.copy2(os.path.join(GEN, f), strona)
    dni = sorted(f[:-3] for f in os.listdir(os.path.join(TU, 'dane-testowe')) if re.fullmatch(r'\d{4}-\d{2}-\d{2}\.md', f))
    for d in dni:
        shutil.copy2(os.path.join(TU, 'dane-testowe', d + '.md'), raporty)
    spec = importlib.util.spec_from_file_location('md2strona', os.path.join(strona, 'md2strona.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    m.main(dni[-1])
    return os.path.join(strona, dni[-1]), strona


def main():
    odswiez_generator()
    folder, strona = generuj()
    wynik, bledy = {}, []
    for f in sorted(os.listdir(folder)):
        if not f.endswith('.html'):
            continue
        t = open(os.path.join(folder, f), encoding='utf-8').read()
        t = t.replace('href="../pomelo-raport.css"', 'href="pomelo-raport.css"')
        t = re.sub(r'src="\.\./pomelo-raport\.js[^"]*"', 'src="pomelo-raport.js"', t)
        t = t.replace('<main class="strona">', '<main class="strona">' + BANER, 1)
        t = t.replace('</body>', STOPKA + '</body>', 1)
        t = t.replace('<head>', '<head><meta name="robots" content="noindex">', 1)
        for cel in re.findall(r'(?:href|src)="([^"#]+)"', t):
            if cel.startswith('https://fonts.googleapis.com/'):
                continue
            if cel not in ('pomelo-raport.css', 'pomelo-raport.js') and not os.path.isfile(os.path.join(folder, cel)):
                bledy.append(f'{f}: odwołanie do pliku spoza demo: {cel}')
        tekst = re.sub(r'<(style|script)[^>]*>.*?</\1>', ' ', t, flags=re.S)
        bledy += [f'{f}: adres e-mail w treści' for _ in EMAIL.findall(tekst)]
        bledy += [f'{f}: wygląda na numer telefonu' for _ in TELEFON.findall(re.sub(r'<[^>]+>', ' ', tekst))]
        if 'spotkanie.html' in t:
            bledy.append(f'{f}: link do prototypu spotkania')
        wynik[f] = t
    if 'index.html' not in wynik:
        bledy.append('brak index.html')
    if bledy:
        print('BŁĘDY – site/ NIE został podmieniony:'); [print(' -', b) for b in bledy]; sys.exit(1)
    shutil.rmtree(SITE, ignore_errors=True); os.makedirs(SITE)
    for f, t in wynik.items():
        open(os.path.join(SITE, f), 'w', encoding='utf-8').write(t)
    for f in ('pomelo-raport.css', 'pomelo-raport.js'):
        shutil.copy2(os.path.join(strona, f), SITE)
    shutil.rmtree(BUILD, ignore_errors=True)
    print(f'OK: {len(wynik)} stron demo w {SITE}')


if __name__ == '__main__':
    main()
