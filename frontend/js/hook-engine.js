/*
  MatchIQ Studio V4.0 - Hook Engine UI
  File nuovo e indipendente: non rompe app.js.
  Aggiungi in index.html dopo app.js:
  <script src="/js/hook-engine.js?v=40"></script>
*/
(function initHookEngineUI() {
  function getValue(id, fallback = "") { return document.getElementById(id)?.value?.trim() || fallback; }
  function setValue(id, value) {
    const field = document.getElementById(id);
    if (!field) return;
    field.value = value;
    field.dispatchEvent(new Event("input", { bubbles: true }));
    field.dispatchEvent(new Event("change", { bubbles: true }));
  }
  function notify(message, engine = "Hook Engine") {
    if (typeof setStatus === "function") return setStatus(message, engine);
    const statusBox = document.getElementById("statusBox");
    const engineStatus = document.getElementById("engineStatus");
    if (statusBox) statusBox.textContent = message;
    if (engineStatus) engineStatus.textContent = engine;
  }
  function injectStyle() {
    if (document.getElementById("hookEngineStyle")) return;
    const style = document.createElement("style");
    style.id = "hookEngineStyle";
    style.textContent = `
      .hook-engine-panel{margin:16px 0;border:1px solid rgba(120,255,63,.22);border-radius:18px;padding:16px;background:radial-gradient(circle at top right, rgba(120,255,63,.12), transparent 36%),linear-gradient(180deg, rgba(11,27,51,.84), rgba(7,20,38,.96));box-shadow:0 18px 44px rgba(0,0,0,.20)}
      .hook-engine-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px}
      .hook-engine-head h3{margin:6px 0 0;font-size:20px}.hook-engine-head p{margin:6px 0 0;color:var(--muted);line-height:1.45;font-size:13px}
      .hook-engine-controls{display:grid;grid-template-columns:1fr 1fr auto;gap:10px;align-items:end;margin-bottom:12px}
      .hook-engine-results{display:grid;gap:10px}.hook-card{width:100%;border:1px solid var(--line);border-radius:16px;padding:13px;color:var(--text);background:rgba(255,255,255,.045);text-align:left;transition:.18s ease}
      .hook-card:hover{transform:translateY(-2px);border-color:rgba(120,255,63,.44);box-shadow:0 16px 38px rgba(0,0,0,.26)}
      .hook-card-top{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px}.hook-score{color:#06120d;background:linear-gradient(135deg, var(--accent), #d8ff3f);border-radius:999px;padding:5px 9px;font-size:12px;font-weight:900}
      .hook-angle{color:var(--accent);font-size:12px;font-weight:900;text-transform:uppercase}.hook-text{display:block;font-size:17px;line-height:1.25;letter-spacing:-.2px}.hook-why{display:block;margin-top:8px;color:var(--muted);font-size:12px;line-height:1.35}
      .hook-actions{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}.hook-empty{color:var(--muted);font-size:13px;line-height:1.45}
      @media(max-width:820px){.hook-engine-controls{grid-template-columns:1fr}.hook-engine-head{display:grid}}
    `;
    document.head.appendChild(style);
  }
  function buildPanel() {
    const projectPanel = document.querySelector(".project-panel");
    const formGrid = projectPanel?.querySelector(".form-grid");
    if (!projectPanel || !formGrid || document.getElementById("hookEnginePanel")) return;
    const panel = document.createElement("div");
    panel.className = "hook-engine-panel";
    panel.id = "hookEnginePanel";
    panel.innerHTML = `
      <div class="hook-engine-head"><div><p class="eyebrow">V4 Hook Engine</p><h3>Genera hook che fermano lo scroll</h3><p>Genera 10 hook classificati per score, scegli il migliore e applicalo subito al Reel.</p></div><span class="status-pill">AI Reel Engine</span></div>
      <div class="hook-engine-controls">
        <label>Piattaforma<select id="hookPlatform"><option value="LinkedIn" selected>LinkedIn</option><option value="Instagram">Instagram</option><option value="TikTok">TikTok</option><option value="YouTube Shorts">YouTube Shorts</option></select></label>
        <label>Target<select id="hookTarget"><option value="creator, club, founder" selected>Creator / Club / Founder</option><option value="società sportive">Società sportive</option><option value="allenatori">Allenatori</option><option value="sponsor">Sponsor</option><option value="startup">Startup</option></select></label>
        <button class="primary-btn" id="generateHooksBtn" type="button">✨ Genera Hook AI</button>
      </div>
      <div class="hook-engine-results" id="hookEngineResults"><div class="hook-empty">Scrivi o scegli un tema, poi genera hook. Il migliore potrà diventare il titolo principale del Reel.</div></div>`;
    projectPanel.insertBefore(panel, formGrid.nextSibling);
  }
  function renderHooks(hooks) {
    const box = document.getElementById("hookEngineResults");
    if (!box) return;
    if (!hooks?.length) { box.innerHTML = `<div class="hook-empty">Nessun hook generato.</div>`; return; }
    box.innerHTML = hooks.map((item, index) => `
      <article class="hook-card"><div class="hook-card-top"><span class="hook-angle">${item.angle || `Hook ${index + 1}`}</span><span class="hook-score">${Number(item.score || 0).toFixed(1)}/10</span></div>
      <strong class="hook-text">${item.hook}</strong><small class="hook-why">${item.why_it_works || ""}</small>
      <div class="hook-actions"><button class="primary-btn small-btn" type="button" data-use-hook="${index}">Usa questo hook</button><button class="ghost-btn small-btn" type="button" data-copy-hook="${index}">Copia</button></div></article>`).join("");
    box.querySelectorAll("[data-use-hook]").forEach((button) => button.addEventListener("click", () => {
      const item = hooks[Number(button.dataset.useHook)];
      if (!item) return;
      setValue("title", item.hook);
      if (item.suggested_topic) setValue("topic", item.suggested_topic);
      if (item.suggested_tone) setValue("tone", item.suggested_tone);
      if (item.suggested_cta) setValue("callToAction", item.suggested_cta);
      if (typeof updatePreview === "function") updatePreview();
      notify("Hook applicato. Il Reel ora parte con una frase più forte.", "Hook Engine");
    }));
    box.querySelectorAll("[data-copy-hook]").forEach((button) => button.addEventListener("click", async () => {
      const item = hooks[Number(button.dataset.copyHook)];
      if (!item) return;
      try { await navigator.clipboard.writeText(item.hook); notify("Hook copiato negli appunti.", "Hook Engine"); }
      catch { notify("Hook pronto da copiare manualmente.", "Hook Engine"); }
    }));
  }
  async function handleGenerateHooks() {
    const button = document.getElementById("generateHooksBtn");
    const box = document.getElementById("hookEngineResults");
    if (!button || !box) return;
    const payload = {brand_name:getValue("brandName","MatchIQ Studio"),topic:getValue("topic","Founder Story"),platform:getValue("hookPlatform","LinkedIn"),tone:getValue("tone","cinematic"),target:getValue("hookTarget","creator, club, founder"),count:10};
    try {
      button.disabled = true;
      box.innerHTML = `<div class="hook-empty">Sto generando hook forti per ${payload.platform}...</div>`;
      notify("Hook Engine al lavoro: sto cercando aperture più forti.", "Hook Engine");
      const data = await generateHooks(payload);
      renderHooks(data.hooks || []);
      notify("Hook generati. Scegli quello con più potenziale.", "Hook Engine");
    } catch(error) {
      box.innerHTML = `<div class="hook-empty">Errore: ${error.message}</div>`;
      notify(`Errore Hook Engine: ${error.message}`, "Errore");
    } finally { button.disabled = false; }
  }
  function bind() {
    document.getElementById("generateHooksBtn")?.addEventListener("click", handleGenerateHooks);
    document.querySelectorAll("[data-suggestion='hook']").forEach((button) => button.addEventListener("click", () => {
      document.getElementById("hookEnginePanel")?.scrollIntoView({behavior:"smooth",block:"center"});
      handleGenerateHooks();
    }));
  }
  function init() { injectStyle(); buildPanel(); bind(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
