const generateBtn = document.getElementById("generateBtn");
const generateTopBtn = document.getElementById("generateTopBtn");
const statusBox = document.getElementById("statusBox");
const engineStatus = document.getElementById("engineStatus");
const resultBox = document.getElementById("resultBox");
const reelVideo = document.getElementById("reelVideo");
const downloadLink = document.getElementById("downloadLink");
const renderStationBtn = document.getElementById("renderStationBtn");
const renderProgressBar = document.getElementById("renderProgressBar");
const renderProgressValue = document.getElementById("renderProgressValue");
const renderPhaseLabel = document.getElementById("renderPhaseLabel");
const renderProgressText = document.getElementById("renderProgressText");
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
const sceneLayoutInput = document.getElementById("sceneLayoutInput");
const sceneMotionInput = document.getElementById("sceneMotionInput");
const sceneVoiceInput = document.getElementById("sceneVoiceInput");
const sceneMotionPreset = document.getElementById("sceneMotionPreset");
const sceneDurationInput = document.getElementById("sceneDurationInput");
const voicePreviewBtn = document.getElementById("voicePreviewBtn");
const regenerateSceneBtn = document.getElementById("regenerateSceneBtn");
const voicePreviewStatus = document.getElementById("voicePreviewStatus");

const musicEnabled = document.getElementById("musicEnabled");
const musicVolume = document.getElementById("musicVolume");
const musicMood = document.getElementById("musicMood");
const musicTrack = document.getElementById("musicTrack");
const musicStartSeconds = document.getElementById("musicStartSeconds");
const exportQuality = document.getElementById("exportQuality");
const voiceEnabled = document.getElementById("voiceEnabled");
const voiceVolume = document.getElementById("voiceVolume");
const voiceStyle = document.getElementById("voiceStyle");
const voiceRate = document.getElementById("voiceRate");
const mediaUploadInput = document.getElementById("mediaUploadInput");
const musicUploadInput = document.getElementById("musicUploadInput");
const mediaUploadStatus = document.getElementById("mediaUploadStatus");
const mediaAssetGrid = document.getElementById("mediaAssetGrid");
const autoAssignMediaBtn = document.getElementById("autoAssignMediaBtn");
const clearSceneImageBtn = document.getElementById("clearSceneImageBtn");
const easyCreateBtn = document.getElementById("easyCreateBtn");
const easyBrand = document.getElementById("easyBrand");
const easyGoal = document.getElementById("easyGoal");
const easyTemplate = document.getElementById("easyTemplate");
const easyIdea = document.getElementById("easyIdea");
const directorHook = document.getElementById("directorHook");
const directorPlan = document.getElementById("directorPlan");


let pollTimer = null;
let currentStoryboard = null;
let selectedSceneIndex = 0;
let mediaAssets = [];
let sceneRegenerationCount = 0;

/* ==============================
   MatchIQ Studio V4.6 Auth Gate
   ============================== */
const authShell = document.getElementById("authShell");
const appShell = document.getElementById("appShell");
const authForm = document.getElementById("authForm");
const loginTab = document.getElementById("loginTab");
const registerTab = document.getElementById("registerTab");
const authTitle = document.getElementById("authTitle");
const authSubtitle = document.getElementById("authSubtitle");
const authName = document.getElementById("authName");
const authEmail = document.getElementById("authEmail");
const authPassword = document.getElementById("authPassword");
const authSubmitBtn = document.getElementById("authSubmitBtn");
const authStatus = document.getElementById("authStatus");
const logoutBtn = document.getElementById("logoutBtn");
let authMode = "login";
let currentUser = null;

function setAuthMode(mode) {
  authMode = mode;
  const isRegister = mode === "register";
  loginTab?.classList.toggle("active", !isRegister);
  registerTab?.classList.toggle("active", isRegister);
  document.querySelector(".auth-name-field")?.classList.toggle("hidden", !isRegister);
  if (authTitle) authTitle.textContent = isRegister ? "Crea il tuo account" : "Accedi al tuo workspace";
  if (authSubtitle) authSubtitle.textContent = isRegister ? "Registra il workspace e inizia a creare reel." : "Entra e continua a creare contenuti verticali.";
  if (authSubmitBtn) authSubmitBtn.textContent = isRegister ? "Crea account" : "Accedi";
  if (authPassword) authPassword.autocomplete = isRegister ? "new-password" : "current-password";
  if (authStatus) authStatus.textContent = "Pronto.";
}

function showApp(user) {
  currentUser = user;
  document.body.classList.remove("auth-locked");
  document.body.classList.add("authenticated");
  authShell?.setAttribute("hidden", "hidden");
  appShell?.removeAttribute("aria-hidden");
  const assistant = document.querySelector(".assistant-message-card strong");
  if (assistant) assistant.textContent = `Workspace pronto, ${user.name}.`;
}

function showAuth(message = "Accedi o crea un account per continuare.") {
  document.body.classList.add("auth-locked");
  document.body.classList.remove("authenticated");
  authShell?.removeAttribute("hidden");
  appShell?.setAttribute("aria-hidden", "true");
  if (authStatus) authStatus.textContent = message;
}

async function bootAuth() {
  const cachedUser = typeof getStoredUser === "function" ? getStoredUser() : null;
  const remembered = typeof hasRememberedWorkspace === "function" ? hasRememberedWorkspace() : !!cachedUser;

  if (cachedUser || remembered) {
    showApp(cachedUser || {name: "Creator", email: ""});
    if (authStatus) authStatus.textContent = "Workspace recuperato.";
  }

  try {
    const data = await getCurrentUser();
    if (data?.user) {
      if (typeof setStoredSession === "function") setStoredSession(data);
      showApp(data.user);
    }
  } catch {
    if (!cachedUser && !remembered) {
      showAuth("Accedi oppure registrati per creare il tuo workspace.");
    }
  }
}

loginTab?.addEventListener("click", () => setAuthMode("login"));
registerTab?.addEventListener("click", () => setAuthMode("register"));

authForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    authSubmitBtn.disabled = true;
    authStatus.textContent = authMode === "register" ? "Creo o recupero il workspace..." : "Accesso in corso...";
    const payload = {
      email: authEmail.value.trim(),
      password: authPassword.value,
    };
    const data = authMode === "register"
      ? await registerUser({...payload, name: authName.value.trim() || "Creator"})
      : await loginUser(payload);
    authForm.reset();
    if (authStatus && data.message) authStatus.textContent = data.message;
    showApp(data.user);
  } catch (error) {
    authStatus.textContent = error.message;
    if (authMode === "login" && /primo accesso|registrazione/i.test(error.message)) {
      setAuthMode("register");
      authStatus.textContent = "Se e' il primo accesso, crea l'account una sola volta. Poi MatchIQ Studio lo ricordera'.";
    }
  } finally {
    authSubmitBtn.disabled = false;
  }
});

logoutBtn?.addEventListener("click", async () => {
  await logoutUser().catch(() => {
    if (typeof clearStoredSession === "function") clearStoredSession();
  });
  currentUser = null;
  showAuth("Sessione chiusa.");
});

setAuthMode("login");
bootAuth();


function getValue(id) {
  return document.getElementById(id)?.value?.trim() || "";
}

function setStatus(message, engineMessage = message) {
  statusBox.textContent = message;
  engineStatus.textContent = engineMessage;
}
function updateRenderStation(progress = 0, phase = "Pronto", message = "") {
  const safeProgress = Math.max(0, Math.min(100, Number(progress) || 0));
  if (renderProgressBar) renderProgressBar.style.width = `${safeProgress}%`;
  if (renderProgressValue) renderProgressValue.textContent = `${Math.round(safeProgress)}%`;
  if (renderPhaseLabel) renderPhaseLabel.textContent = phase;
  if (renderProgressText && message) renderProgressText.textContent = message;

  const steps = [
    ["storyboard", 12],
    ["voice", 32],
    ["motion", 52],
    ["encoding", 76],
    ["export", 96],
  ];

  steps.forEach(([name, threshold]) => {
    const step = document.querySelector(`[data-render-step="${name}"]`);
    if (!step) return;
    const small = step.querySelector("small");
    step.classList.toggle("is-done", safeProgress >= threshold);
    step.classList.toggle("is-active", safeProgress < threshold && safeProgress >= Math.max(0, threshold - 24));
    if (small) {
      if (safeProgress >= threshold) small.textContent = "Completato";
      else if (safeProgress >= Math.max(0, threshold - 24)) small.textContent = "In corso";
      else small.textContent = "In attesa";
    }
  });
}


function getAudioSettings() {
  return {
    music_enabled: Boolean(musicEnabled?.checked || musicTrack?.value),
    music_volume: musicTrack?.value ? Math.max(Number(musicVolume?.value || 0.14), 0.55) : Number(musicVolume?.value || 0.14),
    music_mood: musicMood?.value || "cinematic_lift",
    music_track_url: musicTrack?.value || "",
    music_start_seconds: musicTrack?.value ? Math.max(0, Number(musicStartSeconds?.value || 0)) : 0,
    export_quality: exportQuality?.value || "pro_1080p",
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
    visual_layout: "auto",
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

function getMediaTypeFromAsset(assetOrUrl) {
  if (typeof assetOrUrl === "object" && assetOrUrl?.media_type) return assetOrUrl.media_type;
  const url = typeof assetOrUrl === "string" ? assetOrUrl : assetOrUrl?.url || "";
  if (/\.(mp3|wav|m4a|aac|ogg)$/i.test(url)) return "audio";
  return /\.(mp4|mov|webm|m4v)$/i.test(url) ? "video" : "image";
}

function getSceneMediaType(sceneItem) {
  if (!sceneItem?.image_url) return "";
  return sceneItem.media_type || getMediaTypeFromAsset(sceneItem.image_url);
}

function refreshSceneImageOptions() {
  const selectedValue = sceneImageInput.value;
  const visualAssets = mediaAssets.filter((asset) => asset.media_type !== "audio");
  sceneImageInput.innerHTML = `
    <option value="">Nessun media reale</option>
    ${visualAssets.map((asset) => `<option value="${asset.url}">${asset.media_type === "video" ? "VIDEO" : "IMG"} - ${asset.filename}</option>`).join("")}
  `;
  sceneImageInput.value = selectedValue;
}

function refreshMusicTrackOptions() {
  if (!musicTrack) return;
  const selectedValue = musicTrack.value;
  const audioAssets = mediaAssets.filter((asset) => asset.media_type === "audio");
  musicTrack.innerHTML = `
    <option value="">Usa musica generata</option>
    ${audioAssets.map((asset) => `<option value="${asset.url}">${asset.filename}</option>`).join("")}
  `;
  musicTrack.value = selectedValue;
}

function renderMediaAssets() {
  refreshSceneImageOptions();
  refreshMusicTrackOptions();

  if (!mediaAssets.length) {
    mediaAssetGrid.innerHTML = "<div><span></span><b>Nessun media</b><small>Carica immagini, video o musica</small></div>";
    return;
  }

  mediaAssetGrid.innerHTML = mediaAssets.map((asset) => {
    const isVideo = asset.media_type === "video";
    const isAudio = asset.media_type === "audio";
    const preview = isAudio
      ? `<div class="audio-asset-icon">M</div>`
      : isVideo
      ? `<video src="${asset.url}" muted playsinline preload="metadata"></video>`
      : `<img src="${asset.url}" alt="" loading="lazy" />`;
    return `
    <button class="media-card ${isAudio ? "is-audio" : isVideo ? "is-video" : "is-image"}" type="button" data-media-url="${asset.url}" data-media-type="${asset.media_type || "image"}">
      ${preview}
      <span class="media-type-pill">${isAudio ? "AUDIO" : isVideo ? "VIDEO" : "IMG"}</span>
      <b>${asset.filename}</b>
      <small>Usa nella scena selezionata</small>
    </button>`;
  }).join("");

  mediaAssetGrid.querySelectorAll("[data-media-url]").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.mediaType === "audio") {
        if (musicTrack) musicTrack.value = button.dataset.mediaUrl;
        if (musicEnabled) musicEnabled.checked = true;
        if (musicVolume) musicVolume.value = Math.max(Number(musicVolume.value || 0), 0.55);
        setStatus("Traccia selezionata. Puoi scegliere da che secondo far partire la musica.", "Musica");
        return;
      }

      const activeScene = currentStoryboard?.scenes?.[selectedSceneIndex];
      if (!activeScene) return;

      activeScene.image_url = button.dataset.mediaUrl;
      activeScene.media_type = button.dataset.mediaType || getMediaTypeFromAsset(activeScene.image_url);
      activeScene.visual_layout = activeScene.visual_layout || "auto";
      sceneImageInput.value = activeScene.image_url;
      if (sceneLayoutInput) sceneLayoutInput.value = activeScene.visual_layout;
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

  const visualAssets = mediaAssets.filter((asset) => asset.media_type !== "audio");
  if (!visualAssets.length) {
    setStatus("Carica almeno una immagine o un video reale.", "Media");
    return;
  }

  const layoutCycle = ["full", "poster", "split", "quote", "player"];
  currentStoryboard.scenes.forEach((sceneItem, index) => {
    if (!sceneItem.image_url) {
      const asset = visualAssets[index % visualAssets.length];
      sceneItem.image_url = asset.url;
      sceneItem.media_type = asset.media_type || getMediaTypeFromAsset(asset.url);
    }
    if (!sceneItem.media_type && sceneItem.image_url) {
      sceneItem.media_type = getMediaTypeFromAsset(sceneItem.image_url);
    }
    if (!sceneItem.visual_layout || sceneItem.visual_layout === "auto") {
      sceneItem.visual_layout = layoutCycle[index % layoutCycle.length];
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

async function handleMediaUpload(input = mediaUploadInput) {
  const uploadInput = input?.currentTarget || input || mediaUploadInput;
  const files = Array.from(uploadInput.files || []);
  if (!files.length) return;

  try {
    uploadInput.disabled = true;
    const uploaded = [];
    for (const [index, file] of files.entries()) {
      mediaUploadStatus.textContent = `Carico ${index + 1}/${files.length}: ${file.name}`;
      const asset = await uploadMediaAsset(file);
      uploaded.push(asset);
    }
    mediaAssets = [...uploaded, ...mediaAssets.filter((item) => !uploaded.some((asset) => asset.url === item.url))];
    renderMediaAssets();
    uploadInput.value = "";
    const audioCount = uploaded.filter((asset) => asset.media_type === "audio").length;
    const videoCount = uploaded.filter((asset) => asset.media_type === "video").length;
    const imageCount = uploaded.length - videoCount - audioCount;
    mediaUploadStatus.textContent = `Caricati ${uploaded.length} media: ${imageCount} immagini, ${videoCount} video, ${audioCount} audio.`;
  } catch (error) {
    mediaUploadStatus.textContent = error.message;
  } finally {
    uploadInput.disabled = false;
  }
}

function updateTimeline(storyboard = currentStoryboard) {
  const payload = buildPayload();
  const data = storyboard || buildDraftStoryboard(payload);
  timelineList.innerHTML = data.scenes.map((sceneItem, index) => {
    const duration = Math.max(2, Math.round(sceneItem.duration_seconds || 3));
    const sceneMediaType = getSceneMediaType(sceneItem);
    const mediaLabel = sceneMediaType === "video" ? "VIDEO" : sceneMediaType === "image" ? "IMG" : "NO MEDIA";
    const description = `${sceneItem.title || "Scena"} - ${sceneItem.subtitle || ""}`.trim();
    return `
    <li class="${index === selectedSceneIndex ? "selected" : ""}" data-scene-index="${index}" title="${description}">
      <span>${String(index + 1).padStart(2, "0")}</span>
      <p><b>${sceneItem.title}</b> - ${sceneItem.subtitle}</p>
      <small><em>${mediaLabel}</em><strong>${duration}s</strong></small>
      <div class="scene-card-actions">
        <button type="button" data-scene-action="regen" data-scene-index="${index}">Rigenera</button>
        <button type="button" data-scene-action="image" data-scene-index="${index}">Img</button>
        <button type="button" data-scene-action="text" data-scene-index="${index}">Testo</button>
        <button type="button" data-scene-action="preview" data-scene-index="${index}">Preview</button>
      </div>
    </li>`;
  }).join("");

  timelineList.querySelectorAll("li").forEach((item) => {
    item.addEventListener("click", (event) => {
      if (event.target.closest("[data-scene-action]")) return;
      selectScene(Number(item.dataset.sceneIndex));
    });
  });

  timelineList.querySelectorAll("[data-scene-action]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      handleSceneQuickAction(button.dataset.sceneAction, Number(button.dataset.sceneIndex));
    });
  });
}


function handleSceneQuickAction(action, index) {
  selectScene(index);
  if (action === "regen") {
    regenerateSelectedScene();
    return;
  }
  if (action === "image") {
    scrollToStudioSection("media");
    setStatus("Scegli una immagine o un video e verra assegnato alla scena selezionata.", "Media");
    return;
  }
  if (action === "text") {
    sceneSubtitleInput?.focus();
    setStatus("Modifica il testo della scena. La preview si aggiorna subito.", "Testo");
    return;
  }
  if (action === "preview") {
    updatePreviewFromScene();
    document.querySelector(".phone-panel")?.scrollIntoView({ behavior: "smooth", block: "center" });
    setStatus("Preview scena aggiornata.", "Preview");
  }
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
  const activeMediaType = getSceneMediaType(activeScene);
  phoneScreen.dataset.hasImage = activeScene?.image_url ? "true" : "false";
  phoneScreen.dataset.mediaType = activeMediaType || "none";
  phoneScreen.style.backgroundImage = activeScene?.image_url && activeMediaType !== "video"
    ? `linear-gradient(180deg, rgba(0,0,0,.10) 0%, rgba(0,0,0,.24) 48%, rgba(0,0,0,.74) 100%), url("${activeScene.image_url}")`
    : "";
  hookScore.textContent = scoreHook(payload.title);
}

function fillSceneEditor() {
  const activeScene = currentStoryboard?.scenes?.[selectedSceneIndex];
  const disabled = !activeScene;

  [sceneTitleInput, sceneSubtitleInput, sceneVisualInput, sceneImageInput, sceneLayoutInput, sceneMotionInput, sceneVoiceInput, sceneMotionPreset, sceneDurationInput].forEach((input) => {
    if (input) input.disabled = disabled;
  });

  if (!activeScene) {
    sceneEditorTitle.textContent = "Seleziona una scena";
    sceneEditorMeta.textContent = "Draft";
    sceneTitleInput.value = "";
    sceneSubtitleInput.value = "";
    sceneVisualInput.value = "";
    sceneImageInput.value = "";
    if (sceneLayoutInput) sceneLayoutInput.value = "auto";
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
  if (sceneLayoutInput) sceneLayoutInput.value = activeScene.visual_layout || "auto";
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
  const selectedAsset = mediaAssets.find((asset) => asset.url === activeScene.image_url);
  activeScene.media_type = selectedAsset?.media_type || getMediaTypeFromAsset(activeScene.image_url);
  activeScene.visual_layout = sceneLayoutInput?.value || "auto";
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
  if (renderStationBtn) renderStationBtn.disabled = isGenerating;
}

async function pollReel(jobId) {
  const data = await getReelStatus(jobId);
  setStatus(`${data.message} (${data.progress}%)`, `${data.progress}%`);
  updateRenderStation(data.progress, data.message || "Rendering MP4", `MatchIQ Studio sta producendo il video. Stato: ${data.message || "in corso"}.`);

  if (data.status === "done") {
    clearInterval(pollTimer);
    pollTimer = null;

    reelVideo.src = data.render_url;
    downloadLink.href = data.render_url;
    downloadLink.setAttribute("download", data.filename || "MatchIQ Studio-reel.mp4");
    downloadLink.classList.remove("hidden");
    updateRenderStation(100, "Export completato", "Render completato. Puoi vedere l'anteprima o scaricare il file MP4.");

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
    downloadLink?.classList.add("hidden");
    updateRenderStation(8, "Storyboard", "Creo storyboard, struttura narrativa e direzione creativa.");
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

    updateRenderStation(34, "Voice-over e motion", "Storyboard pronto. Preparo voice-over, scene e movimento.");
    const isProExport = (exportQuality?.value || "pro_1080p") !== "draft";
    setStatus(isProExport ? "Storyboard pronto. Avvio export Pro 1080p..." : "Storyboard pronto. Avvio anteprima veloce...", "Render");

    const data = await renderStoryboard({
      storyboard: currentStoryboard,
      tone: payload.tone,
      visual_style: payload.visual_style,
      pacing: payload.pacing,
      ...getAudioSettings(),
    });

    updateRenderStation(58, "Render avviato", "Generazione avviata. MatchIQ Studio sta lavorando su motion, encoding ed export.");
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
    updateRenderStation(0, "Errore render", error.message || "Errore durante la generazione.");
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

[sceneTitleInput, sceneSubtitleInput, sceneVisualInput, sceneImageInput, sceneLayoutInput, sceneMotionInput, sceneVoiceInput, sceneDurationInput].forEach((input) => {
  input?.addEventListener("input", updateSceneFromEditor);
  input?.addEventListener("change", updateSceneFromEditor);
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

[musicEnabled, musicVolume, musicMood, musicTrack, musicStartSeconds, exportQuality, voiceEnabled, voiceVolume, voiceStyle, voiceRate].forEach((input) => {
  input?.addEventListener("input", () => {
    if (input === musicTrack && musicTrack?.value) {
      if (musicEnabled) musicEnabled.checked = true;
      if (musicVolume) musicVolume.value = Math.max(Number(musicVolume.value || 0), 0.55);
    }
    const audioName = musicTrack?.value ? `traccia caricata ${musicTrack.selectedOptions?.[0]?.textContent || ""}` : `${musicMood?.selectedOptions?.[0]?.textContent || "Cinematic"}`;
    const audioState = musicEnabled?.checked ? `Musica ${audioName} attiva` : "Musica disattivata";
    const qualityState = (exportQuality?.value || "pro_1080p") === "draft" ? "Anteprima 720p" : "Export Pro 1080p";
    const voiceState = voiceEnabled?.checked ? `Voice-over ${voiceStyle?.value || "studio"} attivo nell'MP4` : "Voice-over disattivato";
    setStatus(`${audioState}. ${voiceState}. ${qualityState}.`, "Audio");
  });
});

voicePreviewBtn?.addEventListener("click", previewSceneVoice);
regenerateSceneBtn?.addEventListener("click", regenerateSelectedScene);
mediaUploadInput?.addEventListener("change", handleMediaUpload);
musicUploadInput?.addEventListener("change", handleMediaUpload);
autoAssignMediaBtn?.addEventListener("click", autoAssignMediaToScenes);
clearSceneImageBtn?.addEventListener("click", clearSelectedSceneImage);

generateBtn.addEventListener("click", generateReel);
generateTopBtn.addEventListener("click", generateReel);
renderStationBtn?.addEventListener("click", generateReel);

registerServiceWorker();
loadMediaAssets();
updatePreview();
updateRenderStation(0, "Pronto per il render", "Quando premi Crea MP4, MatchIQ Studio mostrerà lo stato della produzione in tempo reale.");

/* ==============================
   MatchIQ Studio V4.3 Easy Creator helpers
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
      callToAction: "Il viaggio e appena iniziato",
      tone: "cinematic",
      visualStyle: "auto",
      pacing: "balanced",
      durationSeconds: 20,
      musicMood: "cinematic_lift",
      voicePreset: "motivational",
      plan: "Visione, problema, sistema, risultato, CTA."
    },
    product: {
      brandName: "MatchIQ Studio",
      title: "Il modo piu semplice per trasformare una idea in un reel pronto.",
      topic: "Promo prodotto",
      callToAction: "Prova MatchIQ Studio",
      tone: "premium",
      visualStyle: "editorial",
      pacing: "balanced",
      durationSeconds: 18,
      musicMood: "premium",
      voicePreset: "premium",
      plan: "Benefit, problema, soluzione, prova, CTA."
    },
    linkedin: {
      brandName: "MatchIQ Studio",
      title: "Non pubblicare di piu. Pubblica contenuti che fanno capire chi sei.",
      topic: "Post LinkedIn trasformato in reel",
      callToAction: "Racconta meglio il tuo brand",
      tone: "startup",
      visualStyle: "data",
      pacing: "balanced",
      durationSeconds: 20,
      musicMood: "bright_launch",
      voicePreset: "natural",
      plan: "Insight, contesto, idea forte, credibilita, CTA."
    },
    sport: {
      brandName: "MatchIQ Studio",
      title: "Ogni partita racconta una storia. Ora puoi trasformarla in contenuto.",
      topic: "Reel sportivo per club e match day",
      callToAction: "Trasforma il match in un reel professionale",
      tone: "premium",
      visualStyle: "sport",
      pacing: "fast",
      durationSeconds: 15,
      musicMood: "sport_hype",
      voicePreset: "energetic",
      plan: "Hook match day, momento chiave, insight, identita club, CTA."
    },
    sponsor: {
      brandName: "MatchIQ Studio",
      title: "Uno sponsor non compra spazio. Compra attenzione.",
      topic: "Promo sponsor per societa sportiva",
      callToAction: "Dai piu valore ai partner del club",
      tone: "provocative",
      visualStyle: "editorial",
      pacing: "balanced",
      durationSeconds: 18,
      musicMood: "premium",
      voicePreset: "premium",
      plan: "Valore, problema, soluzione, prova partner, CTA."
    },
    offer: {
      brandName: "MatchIQ Studio",
      title: "Questa offerta non deve solo essere vista. Deve essere capita subito.",
      topic: "Offerta commerciale",
      callToAction: "Scopri l'offerta",
      tone: "provocative",
      visualStyle: "auto",
      pacing: "fast",
      durationSeconds: 14,
      musicMood: "bright_launch",
      voicePreset: "energetic",
      plan: "Offerta, urgenza, beneficio, prova, CTA."
    },
    beforeAfter: {
      brandName: "MatchIQ Studio",
      title: "Prima perdevi ore. Ora parti da una idea e arrivi a un reel.",
      topic: "Prima e dopo",
      callToAction: "Crea il tuo prossimo reel",
      tone: "cinematic",
      visualStyle: "auto",
      pacing: "balanced",
      durationSeconds: 18,
      musicMood: "emotional",
      voicePreset: "natural",
      plan: "Prima, frizione, trasformazione, risultato, CTA."
    },
  };
  const template = templates[templateName] || templates.founder;
  const fields = ["brandName", "title", "topic", "callToAction", "tone", "visualStyle", "pacing", "durationSeconds"];
  fields.forEach((id) => {
    const field = document.getElementById(id);
    if (field && template[id] !== undefined) field.value = template[id];
  });
  if (musicMood) musicMood.value = template.musicMood || "cinematic";
  if (musicEnabled) musicEnabled.checked = true;
  applyVoicePreset(template.voicePreset || "natural");
  currentStoryboard = null;
  selectedSceneIndex = 0;
  updateTimeline(buildDraftStoryboard(buildPayload()));
  updatePreview();
  if (directorPlan) directorPlan.textContent = template.plan || "Hook forte, sviluppo, prova visiva e CTA.";
  if (directorHook) directorHook.textContent = template.title;
  setStatus(`Template ${templateName} caricato: ritmo, voce, musica e scene impostati.`, "Template");
  scrollToStudioSection("project");
}

function applyVoicePreset(preset) {
  const presets = {
    natural: { style: "studio", rate: -1, voice: 1, music: .12, mood: "Voce naturale, musica presente ma sotto controllo." },
    energetic: { style: "energetic", rate: 1, voice: 1, music: .14, mood: "Voce energica, ritmo piu veloce." },
    premium: { style: "calm", rate: -2, voice: 1, music: .10, mood: "Voce premium, ritmo pulito." },
    motivational: { style: "energetic", rate: 0, voice: 1, music: .13, mood: "Voce motivazionale, tono founder." },
  };
  const config = presets[preset] || presets.natural;
  if (voiceEnabled) voiceEnabled.checked = true;
  if (musicEnabled) musicEnabled.checked = true;
  if (voiceStyle) voiceStyle.value = config.style;
  if (voiceRate) voiceRate.value = config.rate;
  if (voiceVolume) voiceVolume.value = config.voice;
  if (musicVolume) musicVolume.value = config.music;
  if (musicMood) musicMood.value = preset === "motivational" ? "emotional" : preset === "energetic" ? "sport_hype" : preset === "premium" ? "luxury_minimal" : "cinematic_lift";
  document.querySelectorAll("[data-voice-preset]").forEach((button) => {
    button.classList.toggle("is-selected", button.dataset.voicePreset === preset);
  });
  setStatus(config.mood, "Preset");
}

function updateDirectorRecommendation(mood = "default") {
  const brand = easyBrand?.value?.trim() || "MatchIQ Studio";
  const goal = easyGoal?.value || "creare un reel";
  const idea = easyIdea?.value?.trim() || "Una idea forte";
  const moodMap = {
    emotional: `${brand}: la storia che merita di essere vista.`,
    bold: `Se il tuo reel non ferma lo scroll, non esiste.`,
    pro: `${brand} trasforma una idea in un contenuto chiaro e professionale.`,
    default: idea,
  };
  if (directorHook) directorHook.textContent = moodMap[mood] || moodMap.default;
  if (directorPlan) {
    directorPlan.textContent = `Obiettivo: ${goal}. Piano: hook forte, scena problema, scena soluzione, prova visiva, CTA finale.`;
  }
}

function applyEasyCreator() {
  const templateName = easyTemplate?.value || "founder";
  applyStudioTemplate(templateName);

  const brand = easyBrand?.value?.trim();
  const idea = easyIdea?.value?.trim();
  const goal = easyGoal?.value || "";
  if (brand) document.getElementById("brandName").value = brand;
  if (idea) document.getElementById("title").value = idea;
  if (goal) document.getElementById("topic").value = goal;

  updateDirectorRecommendation("default");
  updatePreview();
  scrollToStudioSection("timeline");
  setStatus("Proposta creata. Puoi modificare ogni scena con i pulsanti semplici.", "Easy Creator");
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



  easyCreateBtn?.addEventListener("click", applyEasyCreator);
  [easyBrand, easyGoal, easyTemplate, easyIdea].forEach((input) => {
    input?.addEventListener("input", () => updateDirectorRecommendation("default"));
    input?.addEventListener("change", () => updateDirectorRecommendation("default"));
  });
  document.querySelectorAll("[data-director-mood]").forEach((button) => {
    button.addEventListener("click", () => {
      updateDirectorRecommendation(button.dataset.directorMood);
      if (easyIdea && directorHook) easyIdea.value = directorHook.textContent;
      setStatus("Creative Director aggiornato. Premi Crea proposta per applicarlo.", "AI Director");
    });
  });
  document.querySelectorAll("[data-voice-preset]").forEach((button) => {
    button.addEventListener("click", () => applyVoicePreset(button.dataset.voicePreset));
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
