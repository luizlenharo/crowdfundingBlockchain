import asyncio

from app.config import settings
from app.services.stellarService import StellarCrowdfundingService
from app.utils.helpers import create_donation_memo
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/debug", tags=["debug"])

# Serviço será inicializado no main.py
stellar_service: StellarCrowdfundingService = None


def set_stellar_service(service: StellarCrowdfundingService):
    global stellar_service
    stellar_service = service


@router.get("/memo/{donor_name}/{amount}")
async def test_memo(donor_name: str, amount: float):
    """Testa formato do memo para uma doação"""
    memo = create_donation_memo(donor_name, amount)
    memo_bytes = len(memo.encode("ascii"))

    return {
        "donor_name": donor_name,
        "amount": amount,
        "memo": memo,
        "memo_bytes": memo_bytes,
        "is_valid": memo_bytes <= 28,
        "max_bytes": 28,
    }


@router.get("/account")
async def debug_account():
    """Informações de debug das contas"""
    if not stellar_service:
        return {"error": "Serviço não disponível"}

    try:
        campaign_info = stellar_service.get_account_info(
            stellar_service.campaign_keypair.public_key
        )
        donor_info = stellar_service.get_account_info(
            stellar_service.donor_keypair.public_key
        )

        return {
            "campaign_account": campaign_info,
            "donor_account": donor_info,
            "campaign_config": {
                "title": settings.CAMPAIGN_TITLE,
                "goal": settings.CAMPAIGN_GOAL_XLM,
                "network": settings.STELLAR_NETWORK,
            },
        }
    except Exception as e:
        return {"error": f"Erro ao obter informações: {e}"}


@router.post("/simulate/{count}")
async def simulate_donations(count: int):
    """Simula doações para teste (máximo 5)"""
    if count > 5:
        raise HTTPException(status_code=400, detail="Máximo 5 doações simuladas")

    if not stellar_service:
        raise HTTPException(status_code=500, detail="Serviço não disponível")

    fake_donations = [
        ("Ana Silva", 5.5),
        ("Carlos Santos", 12.0),
        ("Maria Oliveira", 8.75),
        ("João Pedro", 15.25),
        ("Lucia Costa", 20.0),
    ]

    results = []

    for i in range(min(count, len(fake_donations))):
        name, amount = fake_donations[i]

        try:
            stats = await stellar_service.get_campaign_stats()
            if not stats["is_active"]:
                break

            tx_hash = await stellar_service.process_donation(name, amount)
            results.append(
                {"donor": name, "amount": amount, "hash": tx_hash, "success": True}
            )

            await asyncio.sleep(1)

        except Exception as e:
            results.append(
                {"donor": name, "amount": amount, "error": str(e), "success": False}
            )

    return {
        "simulated_donations": results,
        "message": f"{len([r for r in results if r['success']])} doações simuladas com sucesso",
    }
