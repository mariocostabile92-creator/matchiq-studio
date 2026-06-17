# MatchIQ Studio Architecture

MatchIQ Studio e' organizzato come piattaforma modulare. Ogni area del prodotto deve poter evolvere senza diventare dipendente da un unico file o da una singola funzione di render.

## Frontend

```text
frontend/
  components/     UI riutilizzabile
  pages/          viste principali del prodotto
  services/       chiamate API e adattatori dati
  animations/     preset motion, transizioni, timeline UI
  editor/         strumenti di modifica scene, hook, colori, ritmo
  preview/        preview verticale e player
  timeline/       gestione scene, durata, ordine e rigenerazione
  css/            stile globale attuale
  js/             bootstrap legacy temporaneo
```

## Backend

```text
backend/app/
  ai/             Creative Director, Hook Score, script, storyboard
  project/        progetti, brand memory, workspace
  video/          scene, motion plan, transizioni, sottotitoli
  voice/          voice over, speaker, timing parlato
  image/          immagini AI, asset visuali, prompt visivi
  render/         render jobs, MP4, rigenerazione scene
  music/          musica, ritmo, mood, beat map
  analytics/      performance, contenuti, insight
  routers/        API pubbliche
  schemas/        contratti dati
  core/           configurazione
```

## Engine Pipeline

```text
Project Brief
  -> Creative Director Engine
  -> Storyboard
  -> Image Engine
  -> Video Engine
  -> Voice Engine
  -> Music Engine
  -> Render Engine
  -> Publish Engine
  -> Analytics Engine
```

## Regola Chiave

Il render finale non deve essere il primo risultato.

Prima MatchIQ Studio deve generare una struttura modificabile:

1. brief
2. hook
3. storyboard
4. scene
5. motion plan
6. voice plan
7. music plan
8. preview
9. render finale

Questo permette all'utente di modificare una parte senza rigenerare tutto.

## V1 Tecnica

La V1 attuale resta semplice ma viene separata in moduli:

- Creative Director Engine: genera lo storyboard iniziale.
- Render Engine: produce MP4 dalla struttura.
- Reel API: coordina job e stato.

La prossima evoluzione sara' rendere ogni scena un oggetto persistente rigenerabile.

