from backend.app.video.storyboard import ScenePlan, StoryboardPlan
from backend.app.schemas.reel import HookSuggestion


def _clean_text(value: str, fallback: str) -> str:
    value = (value or "").strip()
    return value if value else fallback


def _detect_context(topic: str, brand_name: str) -> str:
    text = f"{topic} {brand_name}".lower()
    if any(word in text for word in ["matchiq tactical", "tactical", "analisi", "partita", "calcio", "football"]):
        return "football_tech"
    if any(word in text for word in ["sponsor", "partner", "commerciale"]):
        return "sponsor"
    if any(word in text for word in ["founder", "startup", "storia", "vision", "visione"]):
        return "founder"
    if any(word in text for word in ["club", "società", "societa", "squadra"]):
        return "club"
    return "generic"


def _score_hook(hook: str, angle: str) -> float:
    score = 8.2
    strong_words = ["nessuno", "pochi", "davvero", "invisibile", "ritardo", "cambia", "vince", "perde", "attenzione"]
    if any(word in hook.lower() for word in strong_words):
        score += 0.55
    if 45 <= len(hook) <= 95:
        score += 0.35
    if hook.endswith("?"):
        score += 0.25
    if "." in hook:
        score += 0.15
    if angle in {"Contrasto", "Verità nascosta", "Provocazione"}:
        score += 0.25
    return round(min(score, 9.9), 1)


def generate_hooks(
    brand_name: str,
    topic: str,
    platform: str = "LinkedIn",
    tone: str = "cinematic",
    target: str = "creator, club, founder",
    count: int = 10,
) -> list[HookSuggestion]:
    brand = _clean_text(brand_name, "MatchIQ Studio")
    topic = _clean_text(topic, "Founder Story")
    platform = _clean_text(platform, "LinkedIn")
    tone = _clean_text(tone, "cinematic")
    context = _detect_context(topic, brand)

    if context == "football_tech":
        raw_hooks = [
            ("Tutti guardano la partita. Pochi la capiscono davvero.", "Verità nascosta"),
            ("Il risultato dice cosa è successo. MatchIQ mostra perché.", "Contrasto"),
            ("Se analizzi ancora una partita come nel 2015, sei già in ritardo.", "Provocazione"),
            ("La differenza tra vincere e perdere spesso è invisibile.", "Tensione"),
            ("Ogni partita lascia indizi. MatchIQ li trova.", "Mistero"),
            ("Le squadre migliori non improvvisano. Analizzano.", "Autorità"),
            ("Non basta vedere il calcio. Bisogna leggerlo.", "Posizionamento"),
            ("Il futuro del calcio non è solo in campo. È nei dati.", "Visione"),
            ("Una partita non è caos. È informazione da interpretare.", "Reframe"),
            ("Chi capisce prima la partita, decide meglio la prossima mossa.", "Beneficio"),
        ]
        suggested_topic = "Football Intelligence / Analisi tattica AI"
        suggested_cta = "Scopri MatchIQ Tactical"
    elif context == "sponsor":
        raw_hooks = [
            ("Uno sponsor non compra spazio. Compra attenzione.", "Contrasto"),
            ("Il vero valore di uno sponsor si vede quando il contenuto funziona.", "Verità nascosta"),
            ("Se il tuo sponsor passa inosservato, stai sprecando valore.", "Provocazione"),
            ("Ogni partner merita contenuti che sembrano professionali.", "Autorità"),
            ("Il contenuto giusto può trasformare uno sponsor in una storia.", "Reframe"),
            ("Non vendere visibilità. Crea percezione.", "Visione"),
            ("Il prossimo sponsor non vuole solo un logo. Vuole impatto.", "Insight"),
            ("Un buon contenuto rende uno sponsor più facile da vendere.", "Beneficio"),
            ("La differenza tra sponsor e partner è il modo in cui lo racconti.", "Contrasto"),
            ("Il valore non è nel cartellone. È nella storia che costruisci.", "Storytelling"),
        ]
        suggested_topic = "Promo sponsor per società sportiva"
        suggested_cta = "Dai più valore ai partner del club"
    elif context == "club":
        raw_hooks = [
            ("Ogni club ha una storia. Pochi la raccontano davvero bene.", "Verità nascosta"),
            ("Una società forte non comunica a caso.", "Autorità"),
            ("Il calcio dilettantistico merita contenuti professionali.", "Posizionamento"),
            ("Non serve essere una big per sembrare una società seria.", "Contrasto"),
            ("Ogni partita può diventare contenuto. Ogni contenuto può creare valore.", "Visione"),
            ("Il modo in cui comunichi cambia il modo in cui ti percepiscono.", "Insight"),
            ("La squadra gioca in campo. Il brand cresce fuori.", "Reframe"),
            ("Se vuoi nuovi sponsor, inizia da come ti presenti.", "Beneficio"),
            ("Un club moderno non pubblica solo risultati. Costruisce identità.", "Autorità"),
            ("Il tuo club vale più di un post fatto di fretta.", "Provocazione"),
        ]
        suggested_topic = "Comunicazione club / contenuti social"
        suggested_cta = "Crea il prossimo contenuto con MatchIQ Studio"
    else:
        raw_hooks = [
            ("Non serve creare più contenuti. Serve crearli meglio.", "Contrasto"),
            ("Il contenuto giusto può cambiare la percezione di un brand.", "Insight"),
            ("Se il tuo Reel non ferma lo scroll, non esiste.", "Provocazione"),
            ("Le idee non bastano. Serve una regia.", "Reframe"),
            ("Il problema non è pubblicare. È farsi ricordare.", "Verità nascosta"),
            ("Un Reel forte non nasce per caso. Si costruisce.", "Autorità"),
            ("Ogni secondo conta. Soprattutto i primi tre.", "Tensione"),
            ("La qualità del contenuto decide quanto vali agli occhi degli altri.", "Posizionamento"),
            ("Il futuro dei contenuti sarà guidato dall'intelligenza creativa.", "Visione"),
            ("Non stai creando un video. Stai costruendo attenzione.", "Reframe"),
        ]
        suggested_topic = topic
        suggested_cta = "Crea il prossimo contenuto con MatchIQ Studio"

    hooks = []
    for hook, angle in raw_hooks[:count]:
        hooks.append(HookSuggestion(
            score=_score_hook(hook, angle),
            hook=hook,
            angle=angle,
            why_it_works=f"Funziona su {platform} perché apre un contrasto chiaro, crea curiosità e si capisce in meno di tre secondi.",
            suggested_topic=suggested_topic,
            suggested_tone=tone,
            suggested_cta=suggested_cta,
        ))
    hooks.sort(key=lambda item: item.score, reverse=True)
    return hooks


def build_storyboard(
    brand_name: str,
    topic: str,
    title: str,
    tone: str,
    call_to_action: str,
    duration_seconds: int,
) -> StoryboardPlan:
    scene_duration = max(2.0, round(duration_seconds / 5, 1))
    is_matchiq = brand_name.strip().lower() == "matchiq"
    is_founder_story = "founder" in topic.lower() or "story" in topic.lower()

    if is_matchiq and is_founder_story:
        scenes = [
            ScenePlan(index=1,title="Tu davanti al PC",visual="Founder al computer, schermo acceso, notte, concentrazione.",camera="Camera lenta con leggero push-in sul volto e sulle mani.",motion="Zoom progressivo, parallax tra volto, tastiera e monitor.",lighting="Luce monitor fredda, riflessi blu, contrasto alto.",voice_over="Non sto costruendo un software.",subtitle="Non sto costruendo un software.",duration_seconds=scene_duration),
            ScenePlan(index=2,title="Campo da calcio",visual="Campo vuoto, linee bianche, atmosfera da partita importante.",camera="Carrellata laterale bassa lungo la linea del campo.",motion="Parallax tra erba, linea laterale e profondita' dello stadio.",lighting="Luci da stadio, fascio luminoso sul terreno.",voice_over="Sto costruendo una visione per il calcio.",subtitle="Sto costruendo una visione per il calcio.",duration_seconds=scene_duration),
            ScenePlan(index=3,title="Codice",visual="Editor con codice, dati, metriche e dashboard tattica.",camera="Zoom sui dettagli, poi reveal della dashboard.",motion="Glitch leggero, scan line, movimento verticale dei layer.",lighting="Neon verde e blu, look tecnico premium.",voice_over="Dati, intelligenza e decisioni migliori.",subtitle="Dati. Intelligenza. Decisioni migliori.",duration_seconds=scene_duration),
            ScenePlan(index=4,title="Logo",visual="Logo MatchIQ su fondo scuro con energia sport-tech.",camera="Reveal centrale con micro-rotazione.",motion="Luce che attraversa il logo, particelle sottili.",lighting="Controluce premium, bordo luminoso.",voice_over="MatchIQ nasce per alzare lo standard.",subtitle="MatchIQ nasce per alzare lo standard.",duration_seconds=scene_duration),
            ScenePlan(index=5,title="CTA",visual="Final frame pulito con payoff e call to action.",camera="Push-in lento sulla frase finale.",motion="Sottotitoli sincronizzati, linea luminosa finale.",lighting="Glow controllato, chiusura elegante.",voice_over=call_to_action,subtitle=call_to_action,duration_seconds=scene_duration),
        ]
    else:
        scenes = [
            ScenePlan(index=1,title="Hook",visual=f"{brand_name} apre con una frase forte e memorabile.",camera="Push-in centrale sul testo e sul soggetto.",motion="Zoom lento e parallax su piu' layer.",lighting="Contrasto alto, luce direzionale.",voice_over=title,subtitle=title,duration_seconds=scene_duration),
            ScenePlan(index=2,title="Contesto",visual=f"Scenario visivo legato a {topic}.",camera="Movimento laterale fluido.",motion="Layer in profondita' con movimento differenziato.",lighting="Mood coerente con il tono scelto.",voice_over=f"Questa e' la storia dietro {brand_name}.",subtitle=f"La storia dietro {brand_name}.",duration_seconds=scene_duration),
            ScenePlan(index=3,title="Sistema",visual="Processo creativo, codice, media e timeline.",camera="Zoom su dettagli operativi.",motion="Transizioni rapide tra elementi.",lighting="Accenti luminosi sui punti chiave.",voice_over="Ogni idea diventa una struttura pronta da produrre.",subtitle="Ogni idea diventa contenuto.",duration_seconds=scene_duration),
            ScenePlan(index=4,title="Brand Reveal",visual=f"Logo {brand_name} con animazione premium.",camera="Reveal centrale.",motion="Luce passante e profondita'.",lighting="Glow elegante, sfondo scuro.",voice_over=f"{brand_name} diventa riconoscibile.",subtitle=f"{brand_name} diventa riconoscibile.",duration_seconds=scene_duration),
            ScenePlan(index=5,title="CTA",visual="Chiusura forte, invito all'azione.",camera="Push-in finale.",motion="Sottotitolo sincronizzato e transizione morbida.",lighting="Chiusura luminosa.",voice_over=call_to_action,subtitle=call_to_action,duration_seconds=scene_duration),
        ]

    return StoryboardPlan(
        brand_name=brand_name,
        topic=topic,
        hook=title,
        creative_direction=f"Tono {tone}, ritmo verticale premium, scene vive e modificabili.",
        music_mood="Cinematic sport-tech, energia crescente, basso morbido.",
        rhythm="Hook rapido, sviluppo visivo, reveal, CTA.",
        scenes=scenes,
    )
