from datetime import datetime
from typing import Dict

from app.config import settings
from app.models.schemas import (
    DonationRecord,
    DonationRequest,
    DonationResponse,
)
from app.services.stellarService import StellarCrowdfundingService
from app.utils.helpers import create_donation_memo, validate_donation_input
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/donations", tags=["donations"])

# Cache de doações e serviço (serão inicializados no main.py)
donations_cache: Dict[str, DonationRecord] = {}
stellarService: StellarCrowdfundingService = None


def set_stellarService(service: StellarCrowdfundingService):
    global stellarService
    stellarService = service


def set_donations_cache(cache: Dict[str, DonationRecord]):
    global donations_cache
    donations_cache = cache


@router.post("/", response_model=DonationResponse)
async def make_donation(donation_request: DonationRequest):
    """Processa uma nova doação"""

    if not stellarService:
        raise HTTPException(status_code=500, detail="Serviço Stellar não disponível")

    donor_name = donation_request.donor_name.strip()
    amount = donation_request.amount

    # Validações
    is_valid, error_msg = validate_donation_input(donor_name, amount)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        stats = await stellarService.get_campaign_stats()

        if not stats["is_active"]:
            return DonationResponse(
                success=False,
                message="Campanha já atingiu a meta! Doações encerradas.",
                donor_name=donor_name,
                amount=amount,
            )

        remaining = settings.CAMPAIGN_GOAL_XLM - stats["total_raised"]
        if amount > remaining:
            return DonationResponse(
                success=False,
                message=f"Doação muito alta! Faltam apenas {remaining:.2f} XLM para atingir a meta",
                donor_name=donor_name,
                amount=amount,
            )

        transaction_hash = await stellarService.process_donation(donor_name, amount)

        # Cache da doação
        donation_key = f"{donor_name}_{transaction_hash[:8]}"
        donations_cache[donation_key] = DonationRecord(
            donor_name=donor_name,
            amount=amount,
            transaction_hash=transaction_hash,
            timestamp=datetime.utcnow().isoformat(),
            memo=create_donation_memo(donor_name, amount),
        )

        return DonationResponse(
            success=True,
            transaction_hash=transaction_hash,
            message=f"Doação de {amount} XLM registrada com sucesso!",
            donor_name=donor_name,
            amount=amount,
        )

    except Exception as e:
        error_msg = str(e)
        print(f"Erro ao processar doação: {error_msg}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao processar doação: {error_msg}"
        )


@router.get("/")
async def get_donations():
    """Retorna todas as doações da campanha"""
    if not stellarService:
        raise HTTPException(status_code=500, detail="Serviço não disponível")

    try:
        stats = await stellarService.get_campaign_stats()
        return {
            "total_raised": stats["total_raised"],
            "goal": settings.CAMPAIGN_GOAL_XLM,
            "progress_percentage": stats["progress_percentage"],
            "is_active": stats["is_active"],
            "donations": stats["donations"],
            "donors_count": stats["donors_count"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar doações: {e}")


@router.get("/top")
async def get_top_donors(limit: int = 10):
    """Retorna maiores doadores"""
    if not stellarService:
        raise HTTPException(status_code=500, detail="Serviço não disponível")

    try:
        stats = await stellarService.get_campaign_stats()
        donations = stats["donations"]

        donor_totals = {}
        for donation in donations:
            name = donation["donor_name"]
            amount = donation["amount"]

            if name in donor_totals:
                donor_totals[name]["total"] += amount
                donor_totals[name]["count"] += 1
            else:
                donor_totals[name] = {
                    "donor_name": name,
                    "total": amount,
                    "count": 1,
                    "first_donation": donation["timestamp"],
                }

        top_donors = sorted(
            donor_totals.values(), key=lambda x: x["total"], reverse=True
        )

        return {
            "top_donors": top_donors[:limit],
            "total_unique_donors": len(donor_totals),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar top doadores: {e}")
