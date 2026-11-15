# Raport jakości – demo

Publiczne demo prototypu „Raport jakości” (raport poranny dla zespołu cateringu dietetycznego), kurs AI Product Heroes, quest Deploy Pilot.

**Wszystkie dane są fikcyjne**: dania, liczby, komentarze klientów i osoby (zamiast imion pracowników są role). Prawdziwy raport jest dostępny tylko dla zespołu firmy.

- `dane-testowe/` – fikcyjne raporty poranne w formacie markdown.
- `generator/` – generator stron (`md2strona.py`) i style.
- `zbuduj_demo.py` – buduje `site/` i sprawdza, że nie ma w nim e-maili, telefonów ani odwołań do plików spoza demo.
- `site/` – gotowa strona, którą publikuje Netlify (`netlify.toml`).

Adres: https://raport-jakosci-demo.netlify.app. Netlify publikuje automatycznie każdą zmianę wysłaną do gałęzi `main` (folder `site/` bez kroku budowania).

Przebudowa po zmianie danych testowych albo generatora (potem commit i push):

```bash
python zbuduj_demo.py
```
