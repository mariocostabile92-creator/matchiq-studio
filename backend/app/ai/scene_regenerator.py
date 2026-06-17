from backend.app.video.storyboard import ScenePlan


SCENE_VARIANTS = {
    "hook": [
        ("Hook", "Aspetta. Qui non stiamo creando un contenuto qualunque.", "Questo non e' un contenuto qualunque."),
        ("Apertura", "La differenza si vede nei primi tre secondi.", "La differenza si vede nei primi tre secondi."),
        ("Break Pattern", "Fermati un secondo. Questa e' la parte che cambia tutto.", "Fermati un secondo. Questa e' la parte che cambia tutto."),
    ],
    "context": [
        ("Contesto", "Dietro ogni idea forte c'e' una storia precisa.", "Dietro ogni idea forte c'e' una storia precisa."),
        ("Scenario", "Il punto non e' pubblicare di piu'. E' comunicare meglio.", "Il punto non e' pubblicare di piu'. E' comunicare meglio."),
        ("Visione", "Quando il messaggio e' chiaro, il contenuto lavora per te.", "Quando il messaggio e' chiaro, il contenuto lavora per te."),
    ],
    "system": [
        ("Sistema", "Strategia, immagini, voce e ritmo nello stesso flusso.", "Strategia, immagini, voce e ritmo nello stesso flusso."),
        ("Produzione", "Da un'idea grezza a una scena pronta da pubblicare.", "Da un'idea grezza a una scena pronta da pubblicare."),
        ("Workflow", "Ogni scena diventa modificabile, rigenerabile, controllabile.", "Ogni scena diventa modificabile, rigenerabile, controllabile."),
    ],
    "cta": [
        ("CTA", "Il prossimo passo e' trasformare l'idea in contenuto.", "Il prossimo passo e' trasformare l'idea in contenuto."),
        ("Finale", "Ora il contenuto non si guarda soltanto. Si ricorda.", "Ora il contenuto non si guarda soltanto. Si ricorda."),
        ("Chiusura", "Se vuoi distinguerti, devi costruire un sistema.", "Se vuoi distinguerti, devi costruire un sistema."),
    ],
}

MOTION_VARIANTS = [
    ("Push-in cinematografico", "Zoom lento con parallax sul soggetto principale."),
    ("Carrellata laterale", "Pan morbido con profondita' tra primo piano e sfondo."),
    ("Reveal verticale", "Movimento dal basso verso l'alto con luce passante."),
    ("Scan dinamico", "Micro glitch, scan line e cambio profondita'."),
]


def _scene_kind(scene: ScenePlan) -> str:
    text = f"{scene.title} {scene.subtitle} {scene.visual}".lower()
    if "cta" in text or "final" in text or "chius" in text:
        return "cta"
    if "sistema" in text or "produzione" in text or "workflow" in text or "codice" in text:
        return "system"
    if scene.index == 1 or "hook" in text:
        return "hook"
    return "context"


def regenerate_scene(scene: ScenePlan, brand_name: str, topic: str, variant_seed: int = 0) -> ScenePlan:
    kind = _scene_kind(scene)
    variants = SCENE_VARIANTS[kind]
    title, subtitle, voice_over = variants[variant_seed % len(variants)]
    camera, motion = MOTION_VARIANTS[(scene.index + variant_seed) % len(MOTION_VARIANTS)]

    visual = scene.visual
    if kind == "hook":
        visual = f"{brand_name} apre con una scena reale, forte, immediata."
    elif kind == "context":
        visual = f"Scenario legato a {topic}, con immagine reale e testo essenziale."
    elif kind == "system":
        visual = "Dettagli di processo, strumenti, timeline e asset in movimento."
    elif kind == "cta":
        visual = "Final frame pulito, brand leggibile e invito all'azione."

    return scene.model_copy(update={
        "title": title,
        "subtitle": subtitle,
        "voice_over": voice_over,
        "visual": visual,
        "camera": camera,
        "motion": motion,
    })
