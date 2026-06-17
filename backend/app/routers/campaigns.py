from fastapi import APIRouter, HTTPException

from backend.app.campaigns.campaign_store import get_campaign, list_campaigns, save_campaign
from backend.app.schemas.campaign import (
    CampaignListResponse,
    CampaignPayload,
    CampaignRecord,
    CampaignSaveResponse,
)

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])


@router.get("", response_model=CampaignListResponse)
def get_campaigns():
    return CampaignListResponse(
        success=True,
        campaigns=list_campaigns(),
    )


@router.get("/{campaign_id}", response_model=CampaignRecord)
def read_campaign(campaign_id: str):
    campaign = get_campaign(campaign_id)

    if not campaign:
        raise HTTPException(status_code=404, detail="Campagna non trovata.")

    return campaign


@router.post("", response_model=CampaignSaveResponse)
def create_campaign(payload: CampaignPayload):
    campaign = save_campaign(payload)

    return CampaignSaveResponse(
        success=True,
        message="Campagna salvata.",
        campaign=campaign,
    )


@router.put("/{campaign_id}", response_model=CampaignSaveResponse)
def update_campaign(campaign_id: str, payload: CampaignPayload):
    campaign = save_campaign(payload, campaign_id=campaign_id)

    return CampaignSaveResponse(
        success=True,
        message="Campagna aggiornata.",
        campaign=campaign,
    )
