from backend.app.video.storyboard import ScenePlan, StoryboardPlan
from backend.app.schemas.reel import HookSuggestion


def _clean_text(value: str, fallback: str) -> str:
    value = (value or "").strip()
    return value if value else fallback


def _detect_context(topic: str, brand_name: str) -> str:
    text = f"{topic} {brand_name}".lower()
    if any(word in text for word in ["sponsor", "partner", "commerciale"]):
        return "sponsor"
    if any(word in text for word in ["matchiq tactical", "tactical", "analisi", "partita", "calcio", "football", "sport", "match day", "highlights"]):
        return "football_tech"
    if any(word in text for word in ["founder", "startup", "storia", "vision", "visione"]):
        return "founder"
    if any(word in text for word in ["club", "societÃ ", "societa", "squadra"]):
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


def _scene_pack(context: str, brand_name: str, topic: str, title: str, call_to_action: str, scene_duration: float) -> tuple[list[ScenePlan], str, str, str]:
    if context == "football_tech":
        scenes = [
            ScenePlan(index=1,title="Match day hook",visual="Campo, luci, tensione pre-partita, testo grande al centro.",camera="Carrellata laterale bassa",motion="Pan veloce con parallax sportivo",lighting="Luci da stadio, verde e blu, contrasto alto.",voice_over=title,subtitle=title,duration_seconds=scene_duration,transition="impact_cut",motion_speed="fast",zoom_level=1.12,text_emphasis=["PARTITA", "STORIA"],particles="light"),
            ScenePlan(index=2,title="Momento chiave",visual="Azione, dettagli campo, giocatore o tifosi in movimento.",camera="Camera dinamica",motion="Zoom punch-in sul dettaglio",lighting="Fasci di luce e profondita.",voice_over="Ogni partita ha un momento che cambia la storia.",subtitle="Ogni partita ha un momento chiave.",duration_seconds=scene_duration,transition="whip_pan",motion_speed="fast",zoom_level=1.14,text_emphasis=["MOMENTO"]),
            ScenePlan(index=3,title="Dati e lettura",visual="Dashboard, numeri, mappa tattica, insight sul match.",camera="Scan verticale",motion="Glitch leggero e reveal dei dati",lighting="Neon sport-tech.",voice_over="La differenza e' leggere quello che gli altri non vedono.",subtitle="Leggi quello che gli altri non vedono.",duration_seconds=scene_duration,transition="data_scan",motion_speed="medium",zoom_level=1.10,text_emphasis=["LEGGI", "VEDONO"]),
            ScenePlan(index=4,title="Identita club",visual=f"Brand {brand_name}, colori sociali, energia del gruppo.",camera="Reveal centrale",motion="Logo reveal e parallax",lighting="Controluce premium.",voice_over=f"{brand_name} trasforma il match in contenuto.",subtitle=f"{brand_name} trasforma il match in contenuto.",duration_seconds=scene_duration,transition="logo_reveal",motion_speed="medium",zoom_level=1.09,text_emphasis=[brand_name.upper()]),
            ScenePlan(index=5,title="CTA",visual="Finale pulito con chiamata all'azione.",camera="Push-in finale",motion="Sottotitolo animato e chiusura luminosa",lighting="Glow elegante.",voice_over=call_to_action,subtitle=call_to_action,duration_seconds=scene_duration,transition="cinematic_cut",motion_speed="medium",zoom_level=1.08,text_emphasis=["REEL", "PROFESSIONALE"]),
        ]
        return scenes, "Match day / sport launch", "Energia sport-tech, tagli rapidi, tensione e reveal finale.", "Hook, momento, insight, identita, CTA."

    if context == "sponsor":
        scenes = [
            ScenePlan(index=1,title="Valore sponsor",visual="Logo partner, prodotto o servizio in contesto premium.",camera="Push-in pulito",motion="Reveal morbido con luce laterale",lighting="Look commerciale, contrasto alto.",voice_over=title,subtitle=title,duration_seconds=scene_duration,transition="premium_fade",motion_speed="medium",zoom_level=1.08,text_emphasis=["SPONSOR", "ATTENZIONE"],particles="none"),
            ScenePlan(index=2,title="Problema",visual="Contenuto anonimo, logo piccolo, attenzione bassa.",camera="Camera statica con micro-zoom",motion="Prima parte scura, reveal progressivo",lighting="Luce ridotta, atmosfera di contrasto.",voice_over="Uno sponsor non deve passare inosservato.",subtitle="Non deve passare inosservato.",duration_seconds=scene_duration,transition="contrast_cut",motion_speed="slow",zoom_level=1.06,text_emphasis=["INOSSERVATO"],particles="none"),
            ScenePlan(index=3,title="Soluzione",visual="Post verticale, brand partner valorizzato, grafica ordinata.",camera="Carrellata verticale",motion="Layer commerciali in profondita",lighting="Premium, verde e blu.",voice_over="Il contenuto giusto aumenta percezione e valore.",subtitle="Aumenta percezione e valore.",duration_seconds=scene_duration,transition="slide_up",motion_speed="medium",zoom_level=1.08,text_emphasis=["VALORE"]),
            ScenePlan(index=4,title="Proof",visual="Esempio visuale di campagna sponsor pronta.",camera="Reveal dettaglio",motion="Zoom sul beneficio",lighting="Spotlight sul messaggio.",voice_over="Ogni partner merita una presentazione professionale.",subtitle="Ogni partner merita una presentazione professionale.",duration_seconds=scene_duration,transition="soft_flash",motion_speed="medium",zoom_level=1.09,text_emphasis=["PROFESSIONALE"]),
            ScenePlan(index=5,title="CTA",visual="CTA chiara, brand e partner in chiusura.",camera="Push-in finale",motion="Linea luminosa finale",lighting="Chiusura elegante.",voice_over=call_to_action,subtitle=call_to_action,duration_seconds=scene_duration,transition="cinematic_cut",motion_speed="medium",zoom_level=1.08,text_emphasis=["PARTNER"]),
        ]
        return scenes, "Sponsor value reel", "Commerciale premium, pulito, centrato sul valore del partner.", "Valore, problema, soluzione, prova, CTA."

    if context == "club":
        scenes = [
            ScenePlan(index=1,title="Identita",visual="Colori club, squadra, campo, tifosi o stemma.",camera="Push-in forte",motion="Parallax tra logo e immagini reali",lighting="Luci sportive, energia alta.",voice_over=title,subtitle=title,duration_seconds=scene_duration,transition="impact_cut",motion_speed="fast",zoom_level=1.12,text_emphasis=["CLUB", "STORIA"]),
            ScenePlan(index=2,title="Community",visual="Persone, staff, tifosi, momento autentico.",camera="Carrellata laterale",motion="Pan emozionale",lighting="Calda ma premium.",voice_over="Un club non e' solo una squadra. E' una comunita'.",subtitle="Non e' solo una squadra.",duration_seconds=scene_duration,transition="whip_pan",motion_speed="medium",zoom_level=1.10,text_emphasis=["COMUNITA"]),
            ScenePlan(index=3,title="Contenuto",visual="Post, reel, immagini e calendario social.",camera="Scan su dashboard",motion="Layer rapidi",lighting="Sport-tech.",voice_over="Ogni storia puo' diventare un contenuto che resta.",subtitle="Ogni storia puo' diventare contenuto.",duration_seconds=scene_duration,transition="data_scan",motion_speed="medium",zoom_level=1.10,text_emphasis=["CONTENUTO"]),
            ScenePlan(index=4,title="Percezione",visual="Brand club piu ordinato, professionale e riconoscibile.",camera="Reveal centrale",motion="Logo e testo in profondita",lighting="Glow controllato.",voice_over="Il modo in cui comunichi cambia come ti percepiscono.",subtitle="Comunichi meglio. Ti percepiscono meglio.",duration_seconds=scene_duration,transition="logo_reveal",motion_speed="medium",zoom_level=1.09,text_emphasis=["PERCEZIONE"]),
            ScenePlan(index=5,title="CTA",visual="Chiusura con invito chiaro.",camera="Push-in finale",motion="Sottotitolo animato",lighting="Chiusura luminosa.",voice_over=call_to_action,subtitle=call_to_action,duration_seconds=scene_duration,transition="cinematic_cut",motion_speed="medium",zoom_level=1.08,text_emphasis=["CREA"]),
        ]
        return scenes, "Club identity reel", "Sportivo, accessibile, centrato su identita e percezione.", "Identita, community, contenuto, percezione, CTA."

    if context == "founder":
        scenes = [
            ScenePlan(index=1,title="Visione",visual="Founder al PC, notte, luce monitor, concentrazione.",camera="Camera lenta con push-in",motion="Zoom progressivo e parallax",lighting="Luce fredda, contrasto alto.",voice_over=title,subtitle=title,duration_seconds=scene_duration,transition="cinematic_cut",motion_speed="slow",zoom_level=1.10,text_emphasis=["VISIONE", "SOFTWARE"]),
            ScenePlan(index=2,title="Problema",visual="Tanti strumenti aperti, confusione, tempo perso.",camera="Scan verticale",motion="Glitch leggero tra schermate",lighting="Neon blu, tensione.",voice_over="Il problema non e' avere idee. E' trasformarle in contenuti forti.",subtitle="Il problema non e' avere idee.",duration_seconds=scene_duration,transition="data_scan",motion_speed="medium",zoom_level=1.10,text_emphasis=["IDEE"]),
            ScenePlan(index=3,title="Sistema",visual="Workspace creativo, storyboard, media, voce e render.",camera="Zoom sui moduli",motion="Reveal a livelli",lighting="Verde e blu, premium tech.",voice_over=f"{brand_name} unisce idea, storyboard, voce e video.",subtitle="Idea. Storyboard. Voce. Video.",duration_seconds=scene_duration,transition="slide_up",motion_speed="medium",zoom_level=1.09,text_emphasis=["VOCE", "VIDEO"]),
            ScenePlan(index=4,title="Risultato",visual="Reel verticale pronto, preview e download MP4.",camera="Reveal centrale",motion="Luce sul risultato finale",lighting="Glow pulito.",voice_over="Un principiante puo' creare un contenuto che sembra professionale.",subtitle="Professionale anche se parti da zero.",duration_seconds=scene_duration,transition="premium_fade",motion_speed="medium",zoom_level=1.09,text_emphasis=["PROFESSIONALE"]),
            ScenePlan(index=5,title="CTA",visual="Logo e payoff finale.",camera="Push-in finale",motion="Sottotitolo sincronizzato",lighting="Chiusura elegante.",voice_over=call_to_action,subtitle=call_to_action,duration_seconds=scene_duration,transition="logo_reveal",motion_speed="medium",zoom_level=1.08,text_emphasis=["INIZIATO"]),
        ]
        return scenes, "Founder story reel", "Narrativo, founder-led, premium ma semplice.", "Visione, problema, sistema, risultato, CTA."

    if any(word in topic.lower() for word in ["prodotto", "product", "offerta", "promo"]):
        scenes = [
            ScenePlan(index=1,title="Benefit",visual="Prodotto o interfaccia protagonista, messaggio chiaro.",camera="Push-in pulito",motion="Reveal morbido",lighting="Commerciale premium.",voice_over=title,subtitle=title,duration_seconds=scene_duration,transition="premium_fade",motion_speed="medium",zoom_level=1.08,text_emphasis=["SEMPLICE", "PRONTO"],particles="none"),
            ScenePlan(index=2,title="Pain",visual="Prima: tempo perso, strumenti diversi, confusione.",camera="Micro-zoom",motion="Contrasto prima/dopo",lighting="Scura nella prima meta, piu luminosa dopo.",voice_over="Prima servivano tempo, competenze e troppi strumenti.",subtitle="Prima: tempo e troppi strumenti.",duration_seconds=scene_duration,transition="contrast_cut",motion_speed="medium",zoom_level=1.08,text_emphasis=["PRIMA"]),
            ScenePlan(index=3,title="Soluzione",visual="Workspace unico con controlli semplici.",camera="Scan dei controlli",motion="Layer ordinati",lighting="Tech pulito.",voice_over="Ora parti da un'idea e arrivi a un reel pronto.",subtitle="Da idea a reel pronto.",duration_seconds=scene_duration,transition="slide_up",motion_speed="medium",zoom_level=1.09,text_emphasis=["REEL"]),
            ScenePlan(index=4,title="Proof",visual="Anteprima MP4, media, voce e render.",camera="Reveal del risultato",motion="Zoom sul player",lighting="Glow finale.",voice_over="Tutto resta modificabile: scene, immagini, voce e ritmo.",subtitle="Scene, immagini, voce e ritmo.",duration_seconds=scene_duration,transition="data_scan",motion_speed="medium",zoom_level=1.09,text_emphasis=["MODIFICABILE"]),
            ScenePlan(index=5,title="CTA",visual="Chiusura con invito.",camera="Push-in finale",motion="Barra luminosa",lighting="Premium.",voice_over=call_to_action,subtitle=call_to_action,duration_seconds=scene_duration,transition="cinematic_cut",motion_speed="medium",zoom_level=1.08,text_emphasis=["PROVA"]),
        ]
        return scenes, "Product promo reel", "Pulito, commerciale, orientato al beneficio.", "Benefit, pain, soluzione, prova, CTA."

    scenes = [
        ScenePlan(index=1,title="Hook",visual=f"{brand_name} apre con una frase forte e memorabile.",camera="Push-in centrale",motion="Zoom lento e parallax",lighting="Contrasto alto.",voice_over=title,subtitle=title,duration_seconds=scene_duration,transition="cinematic_cut",motion_speed="medium",zoom_level=1.09,text_emphasis=["CONTENUTO"]),
        ScenePlan(index=2,title="Contesto",visual=f"Scenario visuale legato a {topic}.",camera="Movimento laterale fluido",motion="Layer in profondita",lighting="Mood coerente.",voice_over=f"Questa e' la storia dietro {brand_name}.",subtitle=f"La storia dietro {brand_name}.",duration_seconds=scene_duration,transition="premium_fade",motion_speed="medium",zoom_level=1.08),
        ScenePlan(index=3,title="Sistema",visual="Processo creativo, media e timeline.",camera="Zoom su dettagli",motion="Transizioni tra elementi",lighting="Accenti luminosi.",voice_over="Ogni idea diventa una struttura pronta da produrre.",subtitle="Ogni idea diventa contenuto.",duration_seconds=scene_duration,transition="data_scan",motion_speed="medium",zoom_level=1.09,text_emphasis=["IDEA"]),
        ScenePlan(index=4,title="Brand Reveal",visual=f"Logo {brand_name} con animazione premium.",camera="Reveal centrale",motion="Luce passante",lighting="Glow elegante.",voice_over=f"{brand_name} diventa riconoscibile.",subtitle=f"{brand_name} diventa riconoscibile.",duration_seconds=scene_duration,transition="logo_reveal",motion_speed="medium",zoom_level=1.08),
        ScenePlan(index=5,title="CTA",visual="Chiusura forte, invito all'azione.",camera="Push-in finale",motion="Sottotitolo sincronizzato",lighting="Chiusura luminosa.",voice_over=call_to_action,subtitle=call_to_action,duration_seconds=scene_duration,transition="cinematic_cut",motion_speed="medium",zoom_level=1.08,text_emphasis=["CREA"]),
    ]
    return scenes, "Universal content reel", "Verticale premium, chiaro e facile da modificare.", "Hook, contesto, sistema, reveal, CTA."


def build_storyboard(
    brand_name: str,
    topic: str,
    title: str,
    tone: str,
    call_to_action: str,
    duration_seconds: int,
) -> StoryboardPlan:
    brand_name = _clean_text(brand_name, "MatchIQ Studio")
    topic = _clean_text(topic, "Founder Story")
    title = _clean_text(title, "Non sto costruendo un software. Sto costruendo una visione.")
    call_to_action = _clean_text(call_to_action, "Crea il prossimo contenuto")
    scene_duration = max(2.0, round(duration_seconds / 5, 1))
    context = _detect_context(topic, brand_name)

    scenes, formula, creative_direction, rhythm = _scene_pack(context, brand_name, topic, title, call_to_action, scene_duration)

    return StoryboardPlan(
        brand_name=brand_name,
        topic=topic,
        hook=title,
        creative_direction=f"{creative_direction} Tono {tone}, scene modificabili e pensate per 9:16.",
        music_mood="Preset coerente con il template: sport, premium, emotional o cinematic.",
        rhythm=rhythm,
        scenes=scenes,
        reel_formula=formula,
        retention_strategy="Hook forte nei primi tre secondi, scene diverse e CTA chiara.",
        overall_hook_score=88 if context == "generic" else 92,
        emotional_score=86 if context in {"founder", "club"} else 82,
        pacing_score=91 if context in {"football_tech", "sponsor"} else 87,
        cta_score=84,
    )

