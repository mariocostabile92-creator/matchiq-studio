from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from backend.app.schemas.reel import (
    HookGenerateRequest,
    HookGenerateResponse,
    ReelCreateRequest,
    ReelJobResponse,
    SceneRegenerateRequest,
    ReelStatusResponse,
    StoryboardRenderRequest,
)
from backend.app.ai.creative_director import build_storyboard, generate_hooks
from backend.app.ai.scene_regenerator import regenerate_scene
from backend.app.render.reel_renderer import render_storyboard
from backend.app.services.reel_engine import build_reel
from backend.app.video.storyboard import StoryboardPlan

router = APIRouter(prefix="/api/reels", tags=["Reels"])

executor = ThreadPoolExecutor(max_workers=1)
JOBS = {}


def _run_reel_job(job_id: str, payload: ReelCreateRequest):
    try:
        JOBS[job_id]["status"] = "processing"
        JOBS[job_id]["progress"] = 18
        JOBS[job_id]["message"] = "Sto preparando direzione creativa e scene..."

        def on_progress(progress: int, message: str):
            JOBS[job_id]["progress"] = progress
            JOBS[job_id]["message"] = message

        filename, _ = build_reel(
            brand_name=payload.brand_name,
            title=payload.title,
            topic=payload.topic,
            tone=payload.tone,
            duration_seconds=payload.duration_seconds,
            call_to_action=payload.call_to_action,
            visual_style=payload.visual_style,
            pacing=payload.pacing,
            music_enabled=payload.music_enabled,
            music_volume=payload.music_volume,
            music_mood=payload.music_mood,
            music_track_url=payload.music_track_url,
            export_quality=payload.export_quality,
            voice_enabled=payload.voice_enabled,
            voice_volume=payload.voice_volume,
            voice_style=payload.voice_style,
            voice_rate=payload.voice_rate,
            on_progress=on_progress,
        )

        JOBS[job_id].update({"status":"done","progress":100,"message":"Reel generato con successo.","filename":filename,"render_url":f"/renders/{filename}","error":None})
    except Exception as exc:
        JOBS[job_id].update({"status":"error","progress":0,"message":"Errore durante la generazione.","error":str(exc)})


def _run_storyboard_render_job(job_id: str, payload: StoryboardRenderRequest):
    try:
        JOBS[job_id]["status"] = "processing"
        JOBS[job_id]["progress"] = 18
        JOBS[job_id]["message"] = "Sto renderizzando lo storyboard modificato..."

        def on_progress(progress: int, message: str):
            JOBS[job_id]["progress"] = progress
            JOBS[job_id]["message"] = message

        filename, _ = render_storyboard(
            storyboard=payload.storyboard,
            tone=payload.tone,
            visual_style=payload.visual_style,
            pacing=payload.pacing,
            quality=payload.export_quality,
            music_enabled=payload.music_enabled,
            music_volume=payload.music_volume,
            music_mood=payload.music_mood,
            music_track_url=payload.music_track_url,
            voice_enabled=payload.voice_enabled,
            voice_volume=payload.voice_volume,
            voice_style=payload.voice_style,
            voice_rate=payload.voice_rate,
            on_progress=on_progress,
        )

        JOBS[job_id].update({"status":"done","progress":100,"message":"Storyboard renderizzato con successo.","filename":filename,"render_url":f"/renders/{filename}","error":None})
    except Exception as exc:
        JOBS[job_id].update({"status":"error","progress":0,"message":"Errore durante il render dello storyboard.","error":str(exc)})


@router.post("/create", response_model=ReelJobResponse)
def create_reel(payload: ReelCreateRequest):
    job_id = uuid4().hex[:12]
    JOBS[job_id] = {"status":"queued","progress":5,"message":"Reel messo in coda.","filename":None,"render_url":None,"error":None}
    executor.submit(_run_reel_job, job_id, payload)
    return ReelJobResponse(success=True, message="Generazione avviata.", job_id=job_id)


@router.post("/render-storyboard", response_model=ReelJobResponse)
def render_edited_storyboard(payload: StoryboardRenderRequest):
    job_id = uuid4().hex[:12]
    JOBS[job_id] = {"status":"queued","progress":5,"message":"Storyboard messo in coda.","filename":None,"render_url":None,"error":None}
    executor.submit(_run_storyboard_render_job, job_id, payload)
    return ReelJobResponse(success=True, message="Render storyboard avviato.", job_id=job_id)


@router.post("/storyboard", response_model=StoryboardPlan)
def create_storyboard(payload: ReelCreateRequest):
    return build_storyboard(
        brand_name=payload.brand_name,
        title=payload.title,
        topic=payload.topic,
        tone=payload.tone,
        duration_seconds=payload.duration_seconds,
        call_to_action=payload.call_to_action,
    )


@router.post("/generate-hooks", response_model=HookGenerateResponse)
def generate_reel_hooks(payload: HookGenerateRequest):
    hooks = generate_hooks(
        brand_name=payload.brand_name,
        topic=payload.topic,
        platform=payload.platform,
        tone=payload.tone,
        target=payload.target,
        count=payload.count,
    )
    return HookGenerateResponse(success=True, message="Hook generati dal MatchIQ Hook Engine.", hooks=hooks)


@router.post("/regenerate-scene")
def regenerate_storyboard_scene(payload: SceneRegenerateRequest):
    return regenerate_scene(
        scene=payload.scene,
        brand_name=payload.brand_name,
        topic=payload.topic,
        variant_seed=payload.variant_seed,
    )


@router.get("/status/{job_id}", response_model=ReelStatusResponse)
def get_reel_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trovato.")
    return ReelStatusResponse(success=True,status=job["status"],message=job["message"],progress=job["progress"],render_url=job["render_url"],filename=job["filename"],error=job["error"])
