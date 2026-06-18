async function createReel(payload) {
  const response = await fetch("/api/reels/create", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Errore durante l'avvio della generazione.");
  return data;
}

async function createStoryboard(payload) {
  const response = await fetch("/api/reels/storyboard", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Errore durante la creazione dello storyboard.");
  return data;
}

async function generateHooks(payload) {
  const response = await fetch("/api/reels/generate-hooks", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Errore durante la generazione degli hook.");
  return data;
}

async function renderStoryboard(payload) {
  const response = await fetch("/api/reels/render-storyboard", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  let data = {};
  try { data = await response.json(); } catch { data = { detail: response.statusText }; }
  if (!response.ok) {
    if (response.status === 404 || response.status === 405) {
      const scenes = payload.storyboard?.scenes || [];
      const fallbackScene = scenes[0];
      const lastScene = scenes.at(-1);
      return createReel({
        brand_name: payload.storyboard?.brand_name || "MatchIQ Studio",
        title: payload.storyboard?.hook || fallbackScene?.subtitle || "Una persona. Un intero team creativo.",
        topic: payload.storyboard?.topic || fallbackScene?.title || "Founder Story",
        tone: payload.tone || "cinematic",
        visual_style: payload.visual_style || "auto",
        pacing: payload.pacing || "balanced",
        duration_seconds: Math.max(8, Math.round(scenes.reduce((sum, scene) => sum + (scene.duration_seconds || 3), 0))),
        call_to_action: lastScene?.subtitle || "Scopri il progetto",
        music_enabled: payload.music_enabled ?? false,
        music_volume: payload.music_volume ?? 0.08,
        voice_enabled: payload.voice_enabled ?? true,
        voice_volume: payload.voice_volume ?? 0.95,
        voice_style: payload.voice_style ?? "studio",
        voice_rate: payload.voice_rate ?? -1,
      });
    }
    throw new Error(data.detail || "Errore durante il render dello storyboard.");
  }
  return data;
}

async function getReelStatus(jobId) {
  const response = await fetch(`/api/reels/status/${jobId}`);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Errore durante il controllo del Reel.");
  return data;
}

async function listMediaAssets() {
  const response = await fetch("/api/media");
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Errore durante il caricamento della media library.");
  return data;
}

async function uploadMediaAsset(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch("/api/media/upload", {method:"POST",body:formData});
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Errore durante l'upload dell'immagine.");
  return data;
}

async function regenerateScene(payload) {
  const response = await fetch("/api/reels/regenerate-scene", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Errore durante la rigenerazione della scena.");
  return data;
}
