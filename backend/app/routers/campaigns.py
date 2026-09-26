from fastapi import APIRouter, Depends, HTTPException

from backend.app.routers.auth import get_current_user
from backend.app.campaigns.campaign_store import get_campaign, list_campaigns, save_campaign
from backend.app.schemas.campaign import (
    CampaignListResponse,
    CampaignPayload,
    CampaignRecord,
    CampaignSaveResponse,
)

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=CampaignListResponse)
def get_campaigns(current_user=Depends(get_current_user)):
    return CampaignListResponse(
        success=True,
        campaigns=list_campaigns(current_user["id"]),
    )


@router.get("/{campaign_id}", response_model=CampaignRecord)
def read_campaign(campaign_id: str, current_user=Depends(get_current_user)):
    campaign = get_campaign(campaign_id, current_user["id"])

    if not campaign:
        raise HTTPException(status_code=404, detail="Campagna non trovata.")

    return campaign


@router.post("", response_model=CampaignSaveResponse)
def create_campaign(payload: CampaignPayload, current_user=Depends(get_current_user)):
    campaign = save_campaign(payload, current_user["id"])

    if campaign is None:
        raise HTTPException(status_code=404, detail="Progetto non trovato.")

    return CampaignSaveResponse(
        success=True,
        message="Campagna salvata.",
        campaign=campaign,
    )


@router.put("/{campaign_id}", response_model=CampaignSaveResponse)
def update_campaign(campaign_id: str, payload: CampaignPayload, current_user=Depends(get_current_user)):
    campaign = save_campaign(payload, current_user["id"], campaign_id=campaign_id)

    if campaign is None:
        raise HTTPException(status_code=404, detail="Campagna non trovata.")

    return CampaignSaveResponse(
        success=True,
        message="Campagna aggiornata.",
        campaign=campaign,
    )
