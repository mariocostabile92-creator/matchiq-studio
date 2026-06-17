from backend.app.video.storyboard import ScenePlan, StoryboardPlan


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
            ScenePlan(
                index=1,
                title="Tu davanti al PC",
                visual="Founder al computer, schermo acceso, notte, concentrazione.",
                camera="Camera lenta con leggero push-in sul volto e sulle mani.",
                motion="Zoom progressivo, parallax tra volto, tastiera e monitor.",
                lighting="Luce monitor fredda, riflessi blu, contrasto alto.",
                voice_over="Non sto costruendo un software.",
                subtitle="Non sto costruendo un software.",
                duration_seconds=scene_duration,
            ),
            ScenePlan(
                index=2,
                title="Campo da calcio",
                visual="Campo vuoto, linee bianche, atmosfera da partita importante.",
                camera="Carrellata laterale bassa lungo la linea del campo.",
                motion="Parallax tra erba, linea laterale e profondita' dello stadio.",
                lighting="Luci da stadio, fascio luminoso sul terreno.",
                voice_over="Sto costruendo una visione per il calcio.",
                subtitle="Sto costruendo una visione per il calcio.",
                duration_seconds=scene_duration,
            ),
            ScenePlan(
                index=3,
                title="Codice",
                visual="Editor con codice, dati, metriche e dashboard tattica.",
                camera="Zoom sui dettagli, poi reveal della dashboard.",
                motion="Glitch leggero, scan line, movimento verticale dei layer.",
                lighting="Neon verde e blu, look tecnico premium.",
                voice_over="Dati, intelligenza e decisioni migliori.",
                subtitle="Dati. Intelligenza. Decisioni migliori.",
                duration_seconds=scene_duration,
            ),
            ScenePlan(
                index=4,
                title="Logo",
                visual="Logo MatchIQ su fondo scuro con energia sport-tech.",
                camera="Reveal centrale con micro-rotazione.",
                motion="Luce che attraversa il logo, particelle sottili.",
                lighting="Controluce premium, bordo luminoso.",
                voice_over="MatchIQ nasce per alzare lo standard.",
                subtitle="MatchIQ nasce per alzare lo standard.",
                duration_seconds=scene_duration,
            ),
            ScenePlan(
                index=5,
                title="CTA",
                visual="Final frame pulito con payoff e call to action.",
                camera="Push-in lento sulla frase finale.",
                motion="Sottotitoli sincronizzati, linea luminosa finale.",
                lighting="Glow controllato, chiusura elegante.",
                voice_over=call_to_action,
                subtitle=call_to_action,
                duration_seconds=scene_duration,
            ),
        ]
    else:
        scenes = [
            ScenePlan(
                index=1,
                title="Hook",
                visual=f"{brand_name} apre con una frase forte e memorabile.",
                camera="Push-in centrale sul testo e sul soggetto.",
                motion="Zoom lento e parallax su piu' layer.",
                lighting="Contrasto alto, luce direzionale.",
                voice_over=title,
                subtitle=title,
                duration_seconds=scene_duration,
            ),
            ScenePlan(
                index=2,
                title="Contesto",
                visual=f"Scenario visivo legato a {topic}.",
                camera="Movimento laterale fluido.",
                motion="Layer in profondita' con movimento differenziato.",
                lighting="Mood coerente con il tono scelto.",
                voice_over=f"Questa e' la storia dietro {brand_name}.",
                subtitle=f"La storia dietro {brand_name}.",
                duration_seconds=scene_duration,
            ),
            ScenePlan(
                index=3,
                title="Sistema",
                visual="Processo creativo, codice, media e timeline.",
                camera="Zoom su dettagli operativi.",
                motion="Transizioni rapide tra elementi.",
                lighting="Accenti luminosi sui punti chiave.",
                voice_over="Ogni idea diventa una struttura pronta da produrre.",
                subtitle="Ogni idea diventa contenuto.",
                duration_seconds=scene_duration,
            ),
            ScenePlan(
                index=4,
                title="Brand Reveal",
                visual=f"Logo {brand_name} con animazione premium.",
                camera="Reveal centrale.",
                motion="Luce passante e profondita'.",
                lighting="Glow elegante, sfondo scuro.",
                voice_over=f"{brand_name} diventa riconoscibile.",
                subtitle=f"{brand_name} diventa riconoscibile.",
                duration_seconds=scene_duration,
            ),
            ScenePlan(
                index=5,
                title="CTA",
                visual="Chiusura forte, invito all'azione.",
                camera="Push-in finale.",
                motion="Sottotitolo sincronizzato e transizione morbida.",
                lighting="Chiusura luminosa.",
                voice_over=call_to_action,
                subtitle=call_to_action,
                duration_seconds=scene_duration,
            ),
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
