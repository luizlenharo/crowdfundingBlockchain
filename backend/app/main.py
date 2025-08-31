from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.schemas import DonationRecord
from app.routes import campaign, debug, donations
from app.services.stellarService import StellarCrowdfundingService

app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

donations_cache: Dict[str, DonationRecord] = {}

try:
    stellar_service = StellarCrowdfundingService()
    print("(Success) Serviço de vaquinha inicializado")

    campaign.set_stellarService(stellar_service)
    donations.set_stellarService(stellar_service)
    donations.set_donations_cache(donations_cache)
    debug.set_stellar_service(stellar_service)

except Exception as e:
    print(f"X Erro ao inicializar: {e}")
    stellar_service = None

app.include_router(campaign.router)
app.include_router(donations.router)
app.include_router(debug.router)


@app.get("/")
async def root():
    return {
        "message": "Stellar Crowdfunding System",
        "campaign": settings.CAMPAIGN_TITLE,
        "goal": f"{settings.CAMPAIGN_GOAL_XLM} XLM",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
