from datetime import datetime

from app.config import settings
from app.models.schemas import CampaignInfo
from app.services.stellarService import StellarCrowdfundingService
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/campaign", tags=["campaign"])

# Variável global para o serviço (será inicializada no main.py)
stellarService: StellarCrowdfundingService = None


def set_stellarService(service: StellarCrowdfundingService):
    global stellarService
    stellarService = service


@router.get("/info", response_model=CampaignInfo)
async def get_campaign_info():
    """Retorna informações básicas da campanha"""
    if not stellarService:
        raise HTTPException(status_code=500, detail="Serviço não disponível")

    try:
        stats = await stellarService.get_campaign_stats()

        return CampaignInfo(
            title=settings.CAMPAIGN_TITLE,
            description=settings.CAMPAIGN_DESCRIPTION,
            goal=settings.CAMPAIGN_GOAL_XLM,
            total_raised=stats["total_raised"],
            progress_percentage=stats["progress_percentage"],
            is_active=stats["is_active"],
            donors_count=stats["donors_count"],
            created_at=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao obter info da campanha: {e}"
        )
