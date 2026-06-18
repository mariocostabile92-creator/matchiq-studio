const generateBtn = document.getElementById("generateBtn");
const generateTopBtn = document.getElementById("generateTopBtn");
const statusBox = document.getElementById("statusBox");
const engineStatus = document.getElementById("engineStatus");
const resultBox = document.getElementById("resultBox");
const reelVideo = document.getElementById("reelVideo");
const downloadLink = document.getElementById("downloadLink");
const timelineList = document.getElementById("timelineList");

const previewTitle = document.getElementById("previewTitle");
const previewSubtitle = document.getElementById("previewSubtitle");
const previewBrand = document.getElementById("previewBrand");
const previewKicker = document.getElementById("previewKicker");
const previewMotionNote = document.getElementById("previewMotionNote");
const phoneScreen = document.getElementById("phoneScreen");
const hookScore = document.getElementById("hookScore");
const visualStyle = document.getElementById("visualStyle");
const pacing = document.getElementById("pacing");

const sceneEditorTitle = document.getElementById("sceneEditorTitle");
const sceneEditorMeta = document.getElementById("sceneEditorMeta");
const sceneTitleInput = document.getElementById("sceneTitleInput");
const sceneSubtitleInput = document.getElementById("sceneSubtitleInput");
const sceneVisualInput = document.getElementById("sceneVisualInput");
const sceneImageInput = document.getElementById("sceneImageInput");
const sceneMotionInput = document.getElementById("sceneMotionInput");
const sceneVoiceInput = document.getElementById("sceneVoiceInput");
const sceneMotionPreset = document.getElementById("sceneMotionPreset");
const sceneDurationInput = document.getElementById("sceneDurationInput");
const voicePreviewBtn = document.getElementById("voicePreviewBtn");
const regenerateSceneBtn = document.getElementById("regenerateSceneBtn");
const voicePreviewStatus = document.getElementById("voicePreviewStatus");

const musicEnabled = document.getElementById("musicEnabled");
const musicVolume = document.getElementById("musicVolume");
const voiceEnabled = document.getElementById("voiceEnabled");
const voiceVolume = document.getElementById("voiceVolume");
const voiceStyle = document.getElementById("voiceStyle");
const voiceRate = document.getElementById("voiceRate");
const mediaUploadInput = document.getElementById("mediaUploadInput");
const mediaUploadStatus = document.getElementById("mediaUploadStatus");
const mediaAssetGrid = document.getElementById("mediaAssetGrid");
const autoAssignMediaBtn = document.getElementById("autoAssignMediaBtn");
const clearSceneImageBtn = document.getElementById("clearSceneImageBtn");

let pollTimer = null;
let currentStoryboard = null;
let selectedSceneIndex = 0;
let mediaAssets = [];
let sceneRegenerationCount = 0;

function getValue(id) {
  return document.getElementById(id)?.value?.trim() || "";
}

function setStatus(message, engineMessage = message) {
  statusBox.textContent = message;
  engineStatus.textContent = engineMessage;
}

function getAudioSettings() {
  return {
    music_enabled: Boolean(musicEnabled?.checked),
    music_volume: Number(musicVolume?.value || 0.08),
    voice_enabled: Boolean(voiceEnabled?.checked),
    voice_volume: Number(voiceVolume?.value || 0.95),
    voice_style: voiceStyle?.value || "studio",
    voice_rate: Number(voiceRate?.value || -1),
  };
}

function buildPayload() {
  return {
    brand_name: getValue("brandName") || "MatchIQ Studio",
    title: getValue("title") || "Una persona. Un intero team creativo.",
    topic: getValue("topic") || "Founder Story",
    tone: getValue("tone") || "cinematic",
    visual_style: visualStyle?.value || "auto",
    pacing: pacing?.value || "balanced",
    duration_seconds: Number(getValue("durationSeconds") || 20),
    call_to_action: getValue("callToAction") || "Scopri il progetto",
    ...getAudioSettings(),
  };
}

function scene(index, title, subtitle, visual) {
  return {
    index,
    title,
    subtitle,
    visual,
    camera: "Push-in lento",
    motion: "Zoom e parallax leggero",
    lighting: "Contrasto alto",
    voice_over: subtitle,
    image_url: "",
    duration_seconds: 3,
  };
}

function buildDraftStoryboard(payload) {
  return {
    brand_name: payload.brand_name,
    topic: payload.topic,
    hook: payload.title,
    creative_direction: "Draft locale pronto per essere sostituito dal Creative Director.",
    music_mood: "Cinematic sport-tech",
    rhythm: "Hook, sviluppo, reveal, CTA",
    scenes: [
      scene(1, "Hook", payload.title, "Apertura forte con testo e soggetto centrale."),
      scene(2, "Contesto", payload.topic, "Scenario visuale legato al tema."),
      scene(3, "Sistema", "Un intero team creativo", "Processo creativo, timeline e media."),
      scene(4, "Produzione", "Idee, copy, grafiche, video", "Sequenza rapida di elementi produttivi."),
      scene(5, "CTA", payload.call_to_action, "Chiusura pulita con brand e invito all'azione."),
    ],
  };
}

function scoreHook(title) {
  const strongOpen = /non|mai|perche|perche'|questa volta|visione|mondo|miglior/i.test(title);
  const concise = title.length >= 28 && title.length <= 92;
  const contrast = title.includes(".") || title.includes("?") || title.includes("!");
  return Math.min(98, 76 + (strongOpen ? 8 : 0) + (concise ? 7 : 0) + (contrast ? 5 : 0));
}

function getPreviewMotion(sceneItem) {
  const text = `${sceneItem?.title || ""} ${sceneItem?.camera || ""} ${sceneItem?.motion || ""}`.toLowerCase();

  if (text.includes("laterale") || text.includes("campo")) return "pan";
  if (text.includes("logo") || text.includes("reveal")) return "reveal";
  if (text.includes("codice") || text.includes("glitch") || text.includes("scan")) return "scan";
  return "push";
}

function refreshSceneImageOptions() {
  const selectedValue = sceneImageInput.value;
  sceneImageInput.innerHTML = `
    <option value="">Nessuna immagine reale</option>
    ${mediaAssets.map((asset) => `<option value="${asset.url}">${asset.filename}</option>`).join("")}
  `;
  sceneImageInput.value = selectedValue;
}

function renderMediaAssets() {
  refreshSceneImageOptions();

  if (!mediaAssets.length) {
    mediaAssetGrid.innerHTML = "<div><span></span><b>Nessuna immagine</b><small>Carica il primo asset</small></div>";
    return;
  }

  mediaAssetGrid.innerHTML = mediaAssets.map((asset) => `
    <button class="media-card" type="button" data-media-url="${asset.url}">
      <img src="${asset.url}" alt="" />
      <b>${asset.filename}</b>
      <small>Usa nella scena selezionata</small>
    </button>
  `).join("");

  mediaAssetGrid.querySelectorAll("[data-media-url]").forEach((button) => {
    button.addEventListener("click", () => {
      const activeScene = currentStoryboard?.scenes?.[selectedSceneIndex];
      if (!activeScene) return;

      activeScene.image_url = button.dataset.mediaUrl;
      sceneImageInput.value = activeScene.image_url;
      updatePreviewFromScene();
      setStatus("Immagine assegnata alla scena selezionata.", "Media");
    });
  });
}

function autoAssignMediaToScenes() {
  if (!currentStoryboard?.scenes?.length) {
    setStatus("Crea prima uno storyboard.", "Media");
    return;
  }

  if (!mediaAssets.length) {
    setStatus("Carica almeno una immagine reale.", "Media");
    return;
  }

  currentStoryboard.scenes.forEach((sceneItem, index) => {
    if (!sceneItem.image_url) {
      sceneItem.image_url = mediaAssets[index % mediaAssets.length].url;
    }
  });

  fillSceneEditor();
  updateTimeline();
  updatePreviewFromScene();
  setStatus("Immagini distribuite sulle scene vuote.", "Media");
}

function clearSelectedSceneImage() {
  const activeScene = currentStoryboard?.scenes?.[selectedSceneIndex];
  if (!activeScene) return;

  activeScene.image_url = "";
  sceneImageInput.value = "";
  updateTimeline();
  updatePreviewFromScene();
  setStatus("Immagine rimossa dalla scena selezionata.", "Media");
}

async function loadMediaAssets() {
  try {
    mediaAssets = await listMediaAssets();
    renderMediaAssets();
  } catch (error) {
    mediaUploadStatus.textContent = error.message;
  }
}

async function handleMediaUpload() {
  const file = mediaUploadInput.files?.[0];
  if (!file) return;

  try {
    mediaUploadStatus.textContent = "Sto caricando l'immagine...";
    const asset = await uploadMediaAsset(file);
    mediaAssets = [asset, ...mediaAssets.filter((item) => item.url !== asset.url)];
    renderMediaAssets();
    mediaUploadInput.value = "";
    mediaUploadStatus.textContent = "Immagine caricata. Puoi assegnarla alla scena.";
  } catch (error) {
    mediaUploadStatus.textContent = error.message;
  }
}

function updateTimeline(storyboard = currentStoryboard) {
  const payload = buildPayload();
  const data = storyboard || buildDraftStoryboard(payload);
  timelineList.innerHTML = data.scenes.map((sceneItem, index) => `
    <li class="${index === selectedSceneIndex ? "selected" : ""}" data-scene-index="${index}">
      <span>${String(index + 1).padStart(2, "0")}</span>
      <p><b>${sceneItem.title}</b> - ${sceneItem.subtitle}</p>
      <small>${sceneItem.image_url ? "IMG" : ""} ${Math.max(2, Math.round(sceneItem.duration_seconds || 3))}s</small>
    </li>
  `).join("");

  timelineList.querySelectorAll("li").forEach((item) => {
    item.addEventListener("click", () => selectScene(Number(item.dataset.sceneIndex)));
  });
}

function updatePreviewFromScene() {
  const payload = buildPayload();
  const activeScene = currentStoryboard?.scenes?.[selectedSceneIndex];

  previewTitle.textContent = (activeScene?.subtitle || payload.title).toUpperCase();
  previewSubtitle.textContent = activeScene?.visual || payload.topic;
  previewBrand.textContent = payload.brand_name.toUpperCase();
  previewKicker.textContent = activeScene ? `Scena ${activeScene.index} - ${activeScene.title}` : "Live motion preview";
  previewMotionNote.textContent = [activeScene?.camera, activeScene?.motion].filter(Boolean).join(" - ") || "Push-in lento - Parallax";
  phoneScreen.dataset.tone = payload.tone;
  phoneScreen.dataset.motion = getPreviewMotion(activeScene);
  phoneScreen.dataset.visualStyle = payload.visual_style;
  phoneScreen.dataset.hasImage = activeScene?.image_url ? "true" : "false";
  phoneScreen.style.backgroundImage = activeScene?.image_url
    ? `linear-gradient(180deg, rgba(0,0,0,.10) 0%, rgba(0,0,0,.24) 48%, rgba(0,0,0,.74) 100%), url("${activeScene.image_url}")`
    : "";
  hookScore.textContent = scoreHook(payload.title);
}

function fillSceneEditor() {
  const activeScene = currentStoryboard?.scenes?.[selectedSceneIndex];
  const disabled = !activeScene;

  [sceneTitleInput, sceneSubtitleInput, sceneVisualInput, sceneImageInput, sceneMotionInput, sceneVoiceInput, sceneMotionPreset, sceneDurationInput].forEach((input) => {
    input.disabled = disabled;
  });

  if (!activeScene) {
    sceneEditorTitle.textContent = "Seleziona una scena";
    sceneEditorMeta.textContent = "Draft";
    sceneTitleInput.value = "";
    sceneSubtitleInput.value = "";
    sceneVisualInput.value = "";
    sceneImageInput.value = "";
    sceneMotionInput.value = "";
    sceneVoiceInput.value = "";
    sceneMotionPreset.value = "Push-in lento - Zoom e parallax leggero";
    sceneDurationInput.value = "3";
    return;
  }

  sceneEditorTitle.textContent = `Scena ${activeScene.index}: ${activeScene.title}`;
  sceneEditorMeta.textContent = `${Math.round(activeScene.duration_seconds || 3)}s`;
  sceneTitleInput.value = activeScene.title || "";
  sceneSubtitleInput.value = activeScene.subtitle || "";
  sceneVisualInput.value = activeScene.visual || "";
  refreshSceneImageOptions();
  sceneImageInput.value = activeScene.image_url || "";
  sceneMotionInput.value = [activeScene.camera, activeScene.motion].filter(Boolean).join(" - ");
  sceneVoiceInput.value = activeScene.voice_over || "";
  sceneMotionPreset.value = [activeScene.camera, activeScene.motion].filter(Boolean).join(" - ") || "Push-in lento - Zoom e parallax leggero";
  sceneDurationInput.value = activeScene.duration_seconds || 3;
}

function selectScene(index) {
  selectedSceneIndex = index;
  updateTimeline();
  fillSceneEditor();
  updatePreviewFromScene();
}

function updateSceneFromEditor() {
  const activeScene = currentStoryboard?.scenes?.[selectedSceneIndex];
  if (!activeScene) return;

  activeScene.title = sceneTitleInput.value.trim() || activeScene.title;
  activeScene.subtitle = sceneSubtitleInput.value.trim() || activeScene.subtitle;
  activeScene.visual = sceneVisualInput.value.trim() || activeScene.visual;
  activeScene.image_url = sceneImageInput.value;
  const motionParts = sceneMotionInput.value.split(" - ").map((part) => part.trim()).filter(Boolean);
  activeScene.camera = motionParts[0] || activeScene.camera;
  activeScene.motion = motionParts.slice(1).join(" - ") || activeScene.motion;
  activeScene.voice_over = sceneVoiceInput.value.trim() || activeScene.voice_over;
  activeScene.duration_seconds = Number(sceneDurationInput.value || activeScene.duration_seconds || 3);

  updateTimeline();
  fillSceneEditor();
  updatePreviewFromScene();
}

async function regenerateSelectedScene() {
  const activeScene = currentStoryboard?.scenes?.[selectedSceneIndex];
  if (!activeScene) {
    setStatus("Seleziona una scena da rigenerare.", "Scene");
    return;
  }

  try {
    regenerateSceneBtn.disabled = true;
    setStatus(`Rigenero la scena ${activeScene.index}...`, "Scene");
    const payload = buildPayload();
    const regenerated = await regenerateScene({
      scene: activeScene,
      brand_name: payload.brand_name,
      topic: payload.topic,
      variant_seed: sceneRegenerationCount,
    });

    currentStoryboard.scenes[selectedSceneIndex] = {
      ...regenerated,
      image_url: activeScene.image_url || regenerated.image_url || "",
      duration_seconds: activeScene.duration_seconds || regenerated.duration_seconds || 3,
    };
    sceneRegenerationCount += 1;

    updateTimeline();
    fillSceneEditor();
    updatePreviewFromScene();
    setStatus("Scena rigenerata. Puoi modificarla o creare il MP4.", "Scene");
  } catch (error) {
    setStatus(`Errore: ${error.message}`, "Errore");
  } finally {
    regenerateSceneBtn.disabled = false;
  }
}

function previewSceneVoice() {
  if (!("speechSynthesis" in window)) {
    voicePreviewStatus.textContent = "Anteprima voce non disponibile in questo browser.";
    return;
  }

  const activeScene = currentStoryboard?.scenes?.[selectedSceneIndex];
  const text = (sceneVoiceInput.value || sceneSubtitleInput.value || activeScene?.voice_over || activeScene?.subtitle || "").trim();

  if (!text) {
    voicePreviewStatus.textContent = "Scrivi un voice-over per ascoltarlo.";
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "it-IT";
  utterance.rate = Math.max(0.7, Math.min(1.25, 1 + Number(voiceRate?.value || -1) * 0.06));
  utterance.pitch = voiceStyle?.value === "energetic" ? 1 : 0.9;
  utterance.volume = Number(voiceVolume?.value || 0.95);

  utterance.onstart = () => {
    voicePreviewStatus.textContent = "Sto riproducendo la preview voce...";
  };
  utterance.onend = () => {
    voicePreviewStatus.textContent = "Preview completata. Il render MP4 usa la voce locale di Windows.";
  };
  utterance.onerror = () => {
    voicePreviewStatus.textContent = "La preview voce non e' riuscita.";
  };

  window.speechSynthesis.speak(utterance);
}

function updatePreview() {
  const payload = buildPayload();
  currentStoryboard = buildDraftStoryboard(payload);
  selectedSceneIndex = 0;
  updateTimeline();
  fillSceneEditor();
  updatePreviewFromScene();
}

function setGenerating(isGenerating) {
  generateBtn.disabled = isGenerating;
  generateTopBtn.disabled = isGenerating;
}

async function pollReel(jobId) {
  const data = await getReelStatus(jobId);
  setStatus(`${data.message} (${data.progress}%)`, `${data.progress}%`);

  if (data.status === "done") {
    clearInterval(pollTimer);
    pollTimer = null;

    reelVideo.src = data.render_url;
    downloadLink.href = data.render_url;
    downloadLink.setAttribute("download", data.filename || "MatchIQ Studio-reel.mp4");

    resultBox.classList.remove("hidden");
    setGenerating(false);
    setStatus("Reel generato con successo. Puoi guardarlo o scaricarlo.", "Pronto");
    resultBox.scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }

  if (data.status === "error") {
    clearInterval(pollTimer);
    pollTimer = null;
    setGenerating(false);
    setStatus(`Errore: ${data.error || data.message}`, "Errore");
  }
}

async function generateReel() {
  try {
    setGenerating(true);
    resultBox.classList.add("hidden");
    setStatus("Creo storyboard e direzione creativa...", "Storyboard");

    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }

    const payload = buildPayload();
    if (!currentStoryboard || currentStoryboard.hook !== payload.title) {
      currentStoryboard = await createStoryboard(payload);
      selectedSceneIndex = 0;
      updateTimeline();
      fillSceneEditor();
      updatePreviewFromScene();
    }

    setStatus("Storyboard pronto. Avvio render MP4 draft...", "Render");

    const data = await renderStoryboard({
      storyboard: currentStoryboard,
      tone: payload.tone,
      visual_style: payload.visual_style,
      pacing: payload.pacing,
      ...getAudioSettings(),
    });

    setStatus("Generazione avviata. MatchIQ Studio sta lavorando in background...", "In corso");

    pollTimer = setInterval(() => {
      pollReel(data.job_id).catch((error) => {
        console.error(error);
        clearInterval(pollTimer);
        pollTimer = null;
        setGenerating(false);
        setStatus(`Errore: ${error.message}`, "Errore");
      });
    }, 2000);

    await pollReel(data.job_id);
  } catch (error) {
    console.error(error);
    setStatus(`Errore: ${error.message}`, "Errore");
    setGenerating(false);
  }
}

function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return;

  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch((error) => {
      console.warn("Service worker non registrato", error);
    });
  });
}

["brandName", "title", "topic", "tone", "visualStyle", "pacing", "durationSeconds", "callToAction"].forEach((id) => {
  document.getElementById(id)?.addEventListener("input", updatePreview);
  document.getElementById(id)?.addEventListener("change", updatePreview);
});

[sceneTitleInput, sceneSubtitleInput, sceneVisualInput, sceneImageInput, sceneMotionInput, sceneVoiceInput, sceneDurationInput].forEach((input) => {
  input.addEventListener("input", updateSceneFromEditor);
});

sceneMotionPreset.addEventListener("change", () => {
  const [camera, motion] = sceneMotionPreset.value.split(" - ");
  const activeScene = currentStoryboard?.scenes?.[selectedSceneIndex];
  if (!activeScene) return;

  activeScene.camera = camera;
  activeScene.motion = motion;
  sceneMotionInput.value = sceneMotionPreset.value;
  updateTimeline();
  updatePreviewFromScene();
});

[musicEnabled, musicVolume, voiceEnabled, voiceVolume, voiceStyle, voiceRate].forEach((input) => {
  input?.addEventListener("input", () => {
    const audioState = musicEnabled?.checked ? "Musica demo attiva a volume basso" : "Musica demo disattivata";
    const voiceState = voiceEnabled?.checked ? `Voice-over ${voiceStyle?.value || "studio"} attivo nell'MP4` : "Voice-over disattivato";
    setStatus(`${audioState}. ${voiceState}.`, "Audio");
  });
});

voicePreviewBtn?.addEventListener("click", previewSceneVoice);
regenerateSceneBtn?.addEventListener("click", regenerateSelectedScene);
mediaUploadInput?.addEventListener("change", handleMediaUpload);
autoAssignMediaBtn?.addEventListener("click", autoAssignMediaToScenes);
clearSceneImageBtn?.addEventListener("click", clearSelectedSceneImage);

generateBtn.addEventListener("click", generateReel);
generateTopBtn.addEventListener("click", generateReel);

registerServiceWorker();
loadMediaAssets();
updatePreview();

/* ==============================
   MatchIQ Studio V2.3 Dashboard helpers
   ============================== */
function setActiveNavigation(id) {
  document.body.dataset.activeView = id;
  document.body.classList.add("route-transition");
  window.setTimeout(() => document.body.classList.remove("route-transition"), 260);

  document.querySelectorAll("[data-nav-target]").forEach((link) => {
    link.classList.toggle("active", link.dataset.navTarget === id);
  });

  document.querySelectorAll(".nav-list a").forEach((link) => {
    const hrefId = (link.getAttribute("href") || "").replace("#", "");
    link.classList.toggle("active", hrefId === id);
  });
}

function openDashboardView() {
  document.body.classList.remove("studio-editor-open");
  setActiveNavigation("dashboard");
  document.getElementById("dashboard")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function openEditorView(id = "project") {
  document.body.classList.add("studio-editor-open");
  setActiveNavigation(id);
  const target = document.getElementById(id) || document.getElementById("project");
  target?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function scrollToStudioSection(id) {
  if (id === "dashboard") {
    openDashboardView();
    return;
  }

  openEditorView(id);
}

function applyStudioTemplate(templateName) {
  const templates = {
    founder: {
      brandName: "MatchIQ Studio",
      title: "Non sto costruendo un software. Sto costruendo una visione.",
      topic: "Founder Story",
      callToAction: "Il viaggio è appena iniziato",
      tone: "cinematic",
      visualStyle: "auto",
      pacing: "balanced",
    },
    sport: {
      brandName: "MatchIQ Studio",
      title: "Ogni partita racconta una storia. Ora puoi trasformarla in contenuto.",
      topic: "Reel sportivo per club e match day",
      callToAction: "Trasforma il match in un reel professionale",
      tone: "premium",
      visualStyle: "sport",
      pacing: "fast",
    },
    sponsor: {
      brandName: "MatchIQ Studio",
      title: "Uno sponsor non compra spazio. Compra attenzione.",
      topic: "Promo sponsor per società sportiva",
      callToAction: "Dai più valore ai partner del club",
      tone: "provocative",
      visualStyle: "editorial",
      pacing: "balanced",
    },
  };

  const template = templates[templateName] || templates.founder;
  Object.entries(template).forEach(([id, value]) => {
    const field = document.getElementById(id);
    if (field) field.value = value;
  });

  updatePreview();
  setStatus("Template caricato. Puoi modificarlo o creare il Reel MP4.", "Template");
  scrollToStudioSection("project");
}

function bindDashboardEnterpriseActions() {
  document.querySelectorAll("[data-nav-target]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      scrollToStudioSection(link.dataset.navTarget);
    });
  });

  document.getElementById("backToDashboardBtn")?.addEventListener("click", openDashboardView);

  document.querySelectorAll("[data-scroll-target]").forEach((button) => {
    button.addEventListener("click", () => scrollToStudioSection(button.dataset.scrollTarget));
  });

  document.querySelectorAll("[data-template]").forEach((button) => {
    button.addEventListener("click", () => applyStudioTemplate(button.dataset.template));
  });

  document.getElementById("newReelBtn")?.addEventListener("click", () => {
    applyStudioTemplate("founder");
  });

  document.getElementById("sidebarNewReelBtn")?.addEventListener("click", () => {
    applyStudioTemplate("founder");
  });

  document.getElementById("continueProjectBtn")?.addEventListener("click", () => {
    scrollToStudioSection("timeline");
    setStatus("Progetto aperto. Continua dalla timeline o modifica una scena.", "Timeline");
  });

  document.getElementById("openCampaignsBtn")?.addEventListener("click", () => {
    applyStudioTemplate("sponsor");
  });

  document.getElementById("quickTemplateSports")?.addEventListener("click", () => {
    applyStudioTemplate("sport");
  });

  document.querySelectorAll("[data-suggestion]").forEach((button) => {
    button.addEventListener("click", () => {
      const suggestion = button.dataset.suggestion;
      if (suggestion === "hook") {
        const title = document.getElementById("title");
        title.value = "Il contenuto giusto può cambiare la percezione di un club.";
      }
      if (suggestion === "cta") {
        const cta = document.getElementById("callToAction");
        cta.value = "Crea il prossimo contenuto con MatchIQ Studio";
      }
      if (suggestion === "sport") {
        applyStudioTemplate("sport");
        return;
      }
      updatePreview();
      setStatus("Suggerimento AI applicato al progetto.", "AI Assistant");
      scrollToStudioSection("project");
    });
  });
}

bindDashboardEnterpriseActions();


// Studio OS starts from the dashboard, not from the editor.
openDashboardView();


/* ==============================
   MatchIQ Studio V3.0 Workspace micro-interactions
   ============================== */
function animateNumberText(element, target, suffix = "") {
  if (!element) return;
  const finalValue = Number(String(target).replace(/[^0-9.]/g, ""));
  if (!Number.isFinite(finalValue)) return;
  const start = Math.max(0, finalValue - 8);
  const startTime = performance.now();
  const duration = 550;

  function tick(now) {
    const progress = Math.min(1, (now - startTime) / duration);
    const eased = 1 - Math.pow(1 - progress, 3);
    element.textContent = `${Math.round(start + (finalValue - start) * eased)}${suffix}`;
    if (progress < 1) requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}

function pulseEditorWorkspace() {
  const shell = document.getElementById("studioEditorShell");
  if (!shell) return;
  shell.classList.remove("workspace-pulse");
  void shell.offsetWidth;
  shell.classList.add("workspace-pulse");
}

const originalOpenEditorView = typeof openEditorView === "function" ? openEditorView : null;
if (originalOpenEditorView) {
  openEditorView = function(id = "project") {
    originalOpenEditorView(id);
    pulseEditorWorkspace();
  };
}

window.addEventListener("load", () => {
  animateNumberText(document.getElementById("hookScore"), document.getElementById("hookScore")?.textContent || 96);
  animateNumberText(document.getElementById("creativeScoreMini"), 96, "%");
});
