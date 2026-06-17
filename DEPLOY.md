# MatchIQ Studio deploy preview

## Stato

Il progetto e' pronto per una preview online privata.

Funziona:
- frontend servito da FastAPI
- API storyboard/render/media
- upload immagini
- render MP4
- PWA installabile su HTTPS

Limiti noti:
- il voice-over locale usa Windows/PowerShell; su hosting Linux potrebbe non generare voce
- upload e render usano filesystem locale; serve storage persistente per produzione
- i job di render sono in memoria; serve coda persistente per produzione

## Deploy rapido su Railway/Render

Start command:

```text
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

File gia' presenti:
- `Procfile`
- `runtime.txt`
- `requirements.txt`

## Prima del deploy

1. Inizializza git nella cartella del progetto.
2. Crea repository GitHub.
3. Pusha il progetto.
4. Collega GitHub a Railway o Render.
5. Usa il comando di start sopra se la piattaforma non legge il `Procfile`.

## Dopo il deploy

Controlla:
- `/api/health`
- apertura dashboard
- upload immagine
- render senza voice-over
- manifest PWA in HTTPS
