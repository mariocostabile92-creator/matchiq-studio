# MatchIQ Studio

MatchIQ Studio e' una prima console per creare contenuti verticali. Non e' pensata come semplice generatore di Reel, ma come base di un sistema operativo creativo: brief, storyboard, timeline, brand memory, media library, preview e render MP4.

## Avvio locale

```powershell
.\.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Poi apri:

```text
http://127.0.0.1:8000
```

## Deploy preview

Il progetto include un `Procfile` per deploy su servizi tipo Railway/Render:

```text
web: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Nota importante: il voice-over locale usa la voce di Windows tramite PowerShell. Su hosting Linux il render continua a funzionare, ma la voce esportata nell'MP4 non e' garantita finche' non viene integrato un provider TTS cloud/premium.

Per una preview online va bene. Per una versione pubblica servono storage persistente per upload/render e un motore voice-over cloud.

## Stato attuale

- Frontend statico servito da FastAPI.
- API per creare un Reel MP4 in background.
- Creative Director Engine per generare storyboard e scene prima del render.
- Render Engine separato per produrre MP4 draft piu' velocemente.
- Stili visuali per i toni: cinematografico, provocatorio, premium e startup.
- Architettura modulare pronta per image, video, voice, music, render, project e analytics.

## Pipeline attuale

```text
Brief utente
  -> Creative Director Engine
  -> Storyboard modificabile
  -> Render Engine draft
  -> MP4
```

## Documentazione prodotto

- `docs/PRODUCT_VISION.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`

## Prossimi step consigliati

1. Salvare progetti e brand memory su database.
2. Separare i job di render in una coda persistente.
3. Rendere ogni scena modificabile e rigenerabile singolarmente.
4. Aggiungere motion reale: zoom, parallax, luci e transizioni.
5. Integrare voice over, musica e sottotitoli.
6. Aggiungere upload asset nella media library.

