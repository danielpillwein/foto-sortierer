# 🗂️ FotoSortierer

---

## 🎯 Ziel

Ein performantes Desktop-Tool mit grafischer Oberfläche, das:
- alle **Bilder & Videos** aus einem Quellordner (inkl. Unterordner) lädt,  
- Medien **interaktiv sortieren, löschen oder in Unterordner verschieben** kann,  
- **automatisch nach Dubletten sucht** (optional vor dem Sortieren),  
- **EXIF-Daten jederzeit bearbeiten** lässt (z. B. Aufnahmedatum),  
- den **Sortierfortschritt klar sichtbar** über den gesamten Bildschirm anzeigt,  
- und über ein **Testdaten-Generierungsscript** verfügt, um automatisch Beispielordner mit realistischen Mediendateien zu erstellen.

---

## ⚙️ Hauptfunktionen

| Funktion | Beschreibung |
|-----------|---------------|
| 📂 Quell- & Zielauswahl | Auswahl eines unsortierten Medienordners und eines Zielordners |
| 🧮 Lazy Loading | Nur aktuelles + 1–2 Medien im Speicher |
| 🖼️ Medienanzeige | Bilder, GIFs, WebP, Videos (MP4/MOV/AVI/3GP) |
| 🧠 EXIF-Auswertung | Jahr, Monat, Tag bestimmen (aus Metadaten) |
| ✏️ EXIF-Änderung | Datum jederzeit im GUI änderbar (kein Logging nötig) |
| 🗂️ Automatische Struktur | Zielordner pro Jahr + manuelle Unterordner |
| 💾 Sitzungen | Fortschritt mit Prozentangabe gespeichert |
| 🧹 Dublettenerkennung (optional vor Start) | Hochperformante Erkennung & Löschung |
| 📊 Fortschrittsanzeige | Oben mittig, ganzer Bildschirm, Prozent + Balken |
| 🚀 Performance | Multithreaded Lazy Loading, Hashing-Caching |
| 🔒 Stabilität | Crash-sicher, sofortiges JSON-Update |
| 🧱 Testdatengenerator | Script zur automatischen Erstellung eines Testordners mit Unterordnern und gemischten Mediendateien |
| ⚙️ Settings-Datei | Zentrale `config.json` für benutzerspezifische Einstellungen und Standardpfade |

---

## 🧰 Technologien (Best Practice)

| Bereich | Technologie | Grund |
|----------|--------------|--------|
| GUI | **PyQt6** | Moderne, stabile Qt-Basis für Cross-Platform GUIs |
| Video | **QtMultimedia (PyQt6)** | Nahtlose Integration, Hardwarebeschleunigung |
| Bildverarbeitung | **Pillow (PIL)** | Ausgereift, schnell, EXIF-Unterstützung |
| EXIF-Bearbeitung | **piexif** | Zuverlässiges Lesen/Schreiben von Metadaten |
| Dublettenerkennung | **imagehash + NumPy** | Etablierter pHash-Standard, performant |
| Threading | **concurrent.futures.ThreadPoolExecutor** | High-Performance Multithreading |
| Caching | **Disk-Cache + JSON (persistent)** | Einfach, portabel, schnell |
| Konfiguration | **config.json** | Nutzeranpassbare globale Settings |
| Build | **PyInstaller** | Portable Desktop-Executable |
| Logging | **Python logging** | Standardisierte Logstruktur |

---

## ⚙️ Testdatengenerator

**Datei:** `scripts/test_data_generator.py`  
**Ziel:** Automatisch realistische Testordner generieren mit Unterordnern, Datumsvariationen und verschiedenen Dateitypen.

**Funktion:**  
- Erzeugt Unterordner mit zufälliger Tiefe (1–4 Ebenen)  
- Erstellt Dummy-Dateien mit korrektem Format und realistischen Zeitstempeln  
- Dateiformate:  

| Format | Beschreibung                |
| ------ | --------------------------- |
| .jpg   | häufigster Typ              |
| .jpeg  | Standardvariante            |
| .png   | Transparente Bilder         |
| .mp4   | Videos                      |
| .MOV   | iPhone-Videos               |
| .gif   | animierte Bilder            |
| .avi   | alte Videoformate           |
| .webp  | moderne komprimierte Bilder |
| .3gp   | alte Handyvideos            |

**Technologien:**  
- `os`, `pathlib` → Ordnerstruktur  
- `datetime`, `random` → Zeitstempel  
- `shutil`, `tempfile` → Dateioperationen  
- Optional: Dummy-Inhalt per `PIL.Image.new()` und `cv2.VideoWriter()`

---

## ⚙️ Settings-Datei (`config.json`)

**Ziel:** Benutzerdefinierte Einstellungen und Standardwerte dauerhaft speichern.

**Beispielstruktur:**

```json
{
  "default_source_path": "D:/Fotos_unsortiert",
  "default_destination_path": "D:/Fotos_sortiert",
  "thumbnail_cache_size": 500,
  "dupe_threshold": 5,
  "theme": "dark",
  "test_data_folder": "D:/FotoSortierer_Testdaten"
}
```

**Features:**  
- Einstellungen werden beim Start eingelesen  
- Änderungen in der GUI automatisch zurückgeschrieben  
- Defaultwerte bei erster Nutzung automatisch angelegt  

---

## 🧱 Projektaufbau
```
foto-sortierer/
├── main.py # Einstiegspunkt des Programms
│
├── core/ # Zentrale Logik- und Datenverarbeitung
│ ├── file_manager.py # Dateioperationen (scan, move, delete)
│ ├── metadata_extractor.py # EXIF-Daten lesen
│ ├── exif_manager.py # EXIF-Daten schreiben
│ ├── duplicate_detector.py # Dublettenerkennung (pHash, Multithreading)
│ ├── session_manager.py # Sitzungsverwaltung (save/load)
│ ├── media_loader.py # Lazy Loading & Preload-Queue
│ ├── progress_tracker.py # Fortschrittsanzeige & Berechnung
│ ├── cache_manager.py # Hash- & Thumbnail-Caching
│ └── config_manager.py # Lesen & Schreiben der config.json
│
├── ui/ # Benutzeroberfläche (PyQt6)
│ ├── main_window.py # Startmenü: Prozessauswahl, Wiederaufnahme
│ ├── sorter_view.py # Hauptfenster mit Medienanzeige & Buttons
│ ├── dupe_checker.py # GUI zur Dublettenerkennung
│ └── exif_editor.py # Dialog zum Bearbeiten von EXIF-Daten
│
├── scripts/ # Hilfsskripte & Tools
│ └── test_data_generator.py # Erzeugt Testordner mit Medien & Unterordnern
│
├── assets/ # Icons, Themes, Fonts, evtl. Audio
│ ├── icons/ # SVG-Icons für UI-Buttons
│ └── style.qss # Optionales Stylesheet für Dark/Light Mode
│
├── cache/ # Temporäre Cache-Dateien
│ ├── thumbnails/ # Generierte Vorschaubilder
│ ├── hash_cache.json # Gespeicherte pHash-Ergebnisse
│ └── exif_cache.json # Optionaler EXIF-Zwischenspeicher
│
├── data/ # Sitzungs- und Konfigurationsdaten
│ ├── sessions.json # Fortschritt & aktive Prozesse
│ ├── sessions.bak.json # Backup-Datei für Sitzungen
│ └── config.json # Persistente Benutzer-Einstellungen
│
├── logs/ # Laufzeit- und Fehlerprotokolle
│ ├── app.log # Allgemeine Programmlogs
│ └── errors.log # Fehlermeldungen & Absturzberichte
│
├── requirements.txt # Abhängigkeiten (PyQt6, Pillow, imagehash, etc.)
├── .gitignore # Git-Ausschlussliste
├── README.md # Projektdokumentation
└── LICENSE # (optional) Lizenzdatei
```

**📝 Hinweise:**
- Alle Pfade sind plattformunabhängig mit `pathlib` zu handhaben.  
- Cache- und Logverzeichnisse werden beim ersten Start automatisch erstellt.  
- `config.json` steuert Standardpfade, Sprache, Schwellenwerte und UI-Einstellungen.  
- `scripts/` kann für automatisierte Tests und Performancebenchmarks genutzt werden.  
- Struktur ist so aufgebaut, dass sie sowohl **PyInstaller-kompatibel** als auch **GitHub CI/CD-ready

---

 # 🧭 Roadmap (Phasen 1–10)

### 🏗️ Phase 1 – Grundgerüst & Setup

> Ziel: Projektbasis erstellen, Projektstruktur, Styling-Fundament und erste UI-Grundelemente vorbereiten.

- [x] GitHub-Repository anlegen (`foto-sortierer`)
- [ ] Projektstruktur erstellen  
- [ ] `.gitignore` und `requirements.txt` anlegen  
- [ ] README initial erstellen  
- [ ] Globales Dark-UI-Grundlayout definieren (Style, Abstände, Farben)  
- [ ] Logging-Grundlage einbauen (`logs/app.log`)  
- [ ] Testdatengenerator implementieren (`scripts/test_data_generator.py`)  
- [ ] Erste PyQt6-Fensterstruktur testen  

### 🏁 Phase 2 – Startseite (Sessions-Übersicht)

> Ziel: Die erste nutzbare Oberfläche bauen – Sessionliste, Fortschrittsanzeige in Karten, „Neue Session erstellen“-Flow starten.

- [ ] UI: Startseite mit Session-Karten umsetzen  
- [ ] UI: „Neue Session erstellen“-Button (oben rechts)  
- [ ] Backend: `session_manager.py` → Liste laden/speichern  
- [ ] Backend: Fortschrittswerte aus Sessions berechnen  
- [ ] Dummy-Sessions generieren für Entwicklungsphase  
- [ ] Navigation von Startseite → Neue Session  

### 📝 Phase 3 – Neue Session erstellen

> Ziel: Einspaltiges Formular gemäß Mockup bauen + funktionaler Sessionstart.

- [ ] UI: Formular (Quellordner, Zielordner, Sitzungsname)  
- [ ] UI: Checkbox „Dublettenerkennung aktivieren“ mit Erklärungstext  
- [ ] UI: Buttons „Session starten“ & „Abbrechen“  
- [ ] Backend: neue Session anlegen  
- [ ] Backend: Quell- & Zielordner validieren (`file_manager.py`)  
- [ ] Backend: Defaults über `config_manager.py` laden  
- [ ] Navigation nach erfolgreichem Start → Dublettenscan (falls aktiviert)  

### 🔍 Phase 4 – Dublettenerkennung (Analyse-Screen)

> Ziel: Dubletten-Analyse gemäß Mockup implementieren, bevor die Sortieroberfläche geladen wird.

- [ ] UI: Analyse-Screen mit Fortschrittsbalken & Stats  
- [ ] UI: Button „Scan abbrechen“  
- [ ] Backend: `duplicate_detector.py` – pHash Berechnung  
- [ ] Backend: Multithreaded Hashing (ThreadPoolExecutor)  
- [ ] Backend: Restzeit-Schätzung  
- [ ] Backend: Hash-Cache (`hash_cache.json`)  
- [ ] Navigation: Nach Scan automatische Weiterleitung → manuelle Prüfung  

### 🖼️ Phase 5 – Dubletten manuell prüfen (Paarvergleich)

> Ziel: Die UX-kritische manuelle Dublettenprüfung entwickeln (Bildvergleich links/rechts).

- [ ] UI: Zwei große Bilder nebeneinander  
- [ ] UI: Meta-Infos unter jedem Bild (Datum/Uhrzeit/Kamera/Name)  
- [ ] UI: Fortschrittsanzeige („3 von X Paaren“)  
- [ ] UI: Buttons „Linkes Bild behalten“ / „Rechtes Bild behalten“  
- [ ] Backend: Ermittlung der „unsicheren“ Paare  
- [ ] Backend: Interaktion löschen/überspringen/weiter  
- [ ] Navigation: Nach Abschluss → Sortieransicht  

### 🖼️ Phase 6 – Sortieransicht („Main Page“)

> Ziel: Der wichtigste Screen – interaktive Medienanzeige + Sidebar + Sortierlogik.

- [ ] UI: Header (Session schließen, Fortschritt, Details/Stats)  
- [ ] UI: Medienviewer (Bild/Video) in der Mitte  
- [ ] UI: Sidebar rechts (EXIF, Ordner, Aktionen)  
- [ ] Backend: `media_loader.py` (Lazy Loading + Preload)  
- [ ] Backend: `file_manager.py` → move/delete  
- [ ] Backend: `exif_manager.py` → lesen/ändern  
- [ ] Backend: `progress_tracker.py` → Fortschritt speichern  
- [ ] Navigation: Sortieren → nächstes Bild  
