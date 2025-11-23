# FotoSortierer

Ein performantes Desktop-Tool zum Sortieren von Bildern und Videos.

## Features
- **Medienanzeige**: Bilder, GIFs, WebP, Videos (MP4/MOV/AVI/3GP)
- **Lazy Loading**: Nur aktuelles + 1–2 Medien im Speicher
- **EXIF-Auswertung**: Jahr, Monat, Tag bestimmen
- **Dublettenerkennung**: pHash + NumPy
- **Fortschrittsanzeige**: Über gesamten Bildschirm
- **Testdatengenerator**: Automatische Erstellung von Testdaten

## Installation
1. Repository klonen
2. `pip install -r requirements.txt`
3. `python main.py` (sobald implementiert)

## Projektstruktur
- `core/`: Logik (File Manager, Metadata, etc.)
- `ui/`: Benutzeroberfläche (PyQt6)
- `scripts/`: Hilfsskripte (Testdaten)
- `assets/`: Icons, Styles
- `data/`: Konfigurationen und Sessions
- `logs/`: Logfiles
