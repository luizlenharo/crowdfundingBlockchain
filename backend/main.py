from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset
import os
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
import re

load_dotenv()

app = FastAPI(title="Stellar Crowdfunding System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STELLAR_NETWORK = os.getenv("STELLAR_NETWORK", "testnet")
CAMPAIGN_ACCOUNT_SECRET = os.getenv("CAMPAIGN_ACCOUNT_SECRET")
DONOR_ACCOUNT_SECRET = os.getenv("DONOR_ACCOUNT_SECRET") 
CAMPAIGN_GOAL_XLM = float(os.getenv("CAMPAIGN_GOAL_XLM", "100.0"))
CAMPAIGN_TITLE = os.getenv("CAMPAIGN_TITLE", "Vaquinha Comunitária")
CAMPAIGN_DESCRIPTION = os.getenv("CAMPAIGN_DESCRIPTION", "Ajude nosso projeto!")

server = Server("https://horizon-testnet.stellar.org")
network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE

class DonationRequest(BaseModel):
    donor_name: str
    amount: float

class DonationResponse(BaseModel):
    success: bool
    transaction_hash: str = None
    message: str
    donor_name: str
    amount: float = 0.0

class CampaignInfo(BaseModel):
    title: str
    description: str
    goal: float
    total_raised: float
    progress_percentage: float
    is_active: bool
    donors_count: int
    created_at: str

class DonationRecord(BaseModel):
    donor_name: str
    amount: float
    transaction_hash: str
    timestamp: str
    memo: str

donations_cache: Dict[str, DonationRecord] = {}
campaign_start_time = datetime.utcnow().isoformat()

def create_donation_memo(donor_name: str, amount: float) -> str:
    """Cria memo compacto para doação (máx 28 bytes)"""
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', donor_name).strip()
    
    amount_str = f"{amount:.3f}".rstrip('0').rstrip('.')
    
    memo = f"{clean_name}:{amount_str}"
    
    if len(memo.encode('ascii')) > 28:
        amount_part = f":{amount_str}"
        max_name_length = 28 - len(amount_part.encode('ascii'))
        
        if max_name_length > 3:
            clean_name = clean_name[:max_name_length]
            memo = f"{clean_name}:{amount_str}"
        else:
            initials = ''.join([word[0] for word in clean_name.split() if word])[:3]
            memo = f"{initials}:{amount_str}"
    
    return memo

class StellarCrowdfundingService:
    def __init__(self):
        if not CAMPAIGN_ACCOUNT_SECRET:
            raise ValueError("CAMPAIGN_ACCOUNT_SECRET não configurado")
        if not DONOR_ACCOUNT_SECRET:
            raise ValueError("DONOR_ACCOUNT_SECRET não configurado")
        
        try:
            self.campaign_keypair = Keypair.from_secret(CAMPAIGN_ACCOUNT_SECRET)
            self.donor_keypair = Keypair.from_secret(DONOR_ACCOUNT_SECRET)
            
            print(f"(Success) Campanha configurada: {self.campaign_keypair.public_key}")
            print(f"(Success) Conta doador configurada: {self.donor_keypair.public_key}")
            
        except Exception as e:
            raise ValueError(f"Erro nas chaves Stellar: {e}")
    
    async def process_donation(self, donor_name: str, amount: float) -> str:
        """Processa doação na blockchain Stellar"""
        try:
            donor_account = server.load_account(self.donor_keypair.public_key)
            
            memo_text = create_donation_memo(donor_name, amount)
            
            transaction = (
                TransactionBuilder(
                    source_account=donor_account,
                    network_passphrase=network_passphrase,
                    base_fee=100
                )
                .add_text_memo(memo_text)
                .append_payment_op(
                    destination=self.campaign_keypair.public_key,
                    amount=str(amount),
                    asset=Asset.native()
                )
                .set_timeout(30)
                .build()
            )
            
            transaction.sign(self.donor_keypair)
            response = server.submit_transaction(transaction)
            
            return response["hash"]
            
        except Exception as e:
            raise Exception(f"Erro na transação Stellar: {str(e)}")
    
    async def get_campaign_stats(self) -> Dict:
        """Calcula estatísticas da campanha baseado na blockchain"""
        try:
            transactions = server.transactions().for_account(
                self.campaign_keypair.public_key
            ).limit(200).order(desc=True).call()
            
            total_raised = 0.0
            donations = []
            
            for tx in transactions["_embedded"]["records"]:
                try:
                    operations = server.operations().for_transaction(tx["hash"]).call()
                    
                    for op in operations["_embedded"]["records"]:
                        if (op["type"] == "payment" and 
                            op["to"] == self.campaign_keypair.public_key and
                            op["asset_type"] == "native"):
                            
                            amount = float(op["amount"])
                            total_raised += amount
                            
                            memo = tx.get("memo", "")
                            donor_name = "Anônimo"
                            
                            if memo and ":" in memo:
                                try:
                                    parts = memo.split(":")
                                    donor_name = parts[0] if parts[0] else "Anônimo"
                                except:
                                    pass
                            
                            donations.append({
                                "donor_name": donor_name,
                                "amount": amount,
                                "transaction_hash": tx["hash"],
                                "timestamp": tx["created_at"],
                                "memo": memo
                            })
                            
                except Exception as e:
                    print(f"Erro ao processar operação: {e}")
                    continue
            
            progress = min((total_raised / CAMPAIGN_GOAL_XLM) * 100, 100)
            is_active = total_raised < CAMPAIGN_GOAL_XLM
            
            return {
                "total_raised": total_raised,
                "goal": CAMPAIGN_GOAL_XLM,
                "progress_percentage": progress,
                "is_active": is_active,
                "donations": sorted(donations, key=lambda x: x["timestamp"], reverse=True),
                "donors_count": len(donations)
            }
            
        except Exception as e:
            print(f"Erro ao calcular estatísticas: {e}")
            return {
                "total_raised": 0.0,
                "goal": CAMPAIGN_GOAL_XLM,
                "progress_percentage": 0.0,
                "is_active": True,
                "donations": [],
                "donors_count": 0
            }

try:
    stellar_service = StellarCrowdfundingService()
    print("(Success) Serviço de vaquinha inicializado")
except Exception as e:
    print(f"X Erro ao inicializar: {e}")
    stellar_service = None

@app.get("/")
async def root():
    return {
        "message": "Stellar Crowdfunding System", 
        "campaign": CAMPAIGN_TITLE,
        "goal": f"{CAMPAIGN_GOAL_XLM} XLM",
        "status": "running"
    }

@app.get("/campaign/info")
async def get_campaign_info():
    """Retorna informações básicas da campanha"""
    if not stellar_service:
        raise HTTPException(status_code=500, detail="Serviço não disponível")
    
    try:
        stats = await stellar_service.get_campaign_stats()
        
        return CampaignInfo(
            title=CAMPAIGN_TITLE,
            description=CAMPAIGN_DESCRIPTION,
            goal=CAMPAIGN_GOAL_XLM,
            total_raised=stats["total_raised"],
            progress_percentage=stats["progress_percentage"],
            is_active=stats["is_active"],
            donors_count=stats["donors_count"],
            created_at=campaign_start_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter info da campanha: {e}")

@app.post("/donate", response_model=DonationResponse)
async def make_donation(donation_request: DonationRequest):
    """Processa uma nova doação"""
    
    if not stellar_service:
        raise HTTPException(status_code=500, detail="Serviço Stellar não disponível")
    
    donor_name = donation_request.donor_name.strip()
    amount = donation_request.amount
    
    # Validações
    if not donor_name or len(donor_name) < 2:
        raise HTTPException(status_code=400, detail="Nome deve ter pelo menos 2 caracteres")
    
    if len(donor_name) > 20:
        raise HTTPException(status_code=400, detail="Nome muito longo (máx 20 caracteres)")
    
    if amount < 0.1:
        raise HTTPException(status_code=400, detail="Doação mínima: 0.1 XLM")
    
    if amount > 1000:
        raise HTTPException(status_code=400, detail="Doação máxima: 1000 XLM")
    
    try:
        stats = await stellar_service.get_campaign_stats()
        
        if not stats["is_active"]:
            return DonationResponse(
                success=False,
                message="Campanha já atingiu a meta! Doações encerradas.",
                donor_name=donor_name,
                amount=amount
            )
        
        remaining = CAMPAIGN_GOAL_XLM - stats["total_raised"]
        if amount > remaining:
            return DonationResponse(
                success=False,
                message=f"Doação muito alta! Faltam apenas {remaining:.2f} XLM para atingir a meta",
                donor_name=donor_name,
                amount=amount
            )
        
        transaction_hash = await stellar_service.process_donation(donor_name, amount)
        
        donation_key = f"{donor_name}_{transaction_hash[:8]}"
        donations_cache[donation_key] = DonationRecord(
            donor_name=donor_name,
            amount=amount,
            transaction_hash=transaction_hash,
            timestamp=datetime.utcnow().isoformat(),
            memo=create_donation_memo(donor_name, amount)
        )
        
        return DonationResponse(
            success=True,
            transaction_hash=transaction_hash,
            message=f"Doação de {amount} XLM registrada com sucesso!",
            donor_name=donor_name,
            amount=amount
        )
        
    except Exception as e:
        error_msg = str(e)
        print(f"Erro ao processar doação: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar doação: {error_msg}")

@app.get("/donations")
async def get_donations():
    """Retorna todas as doações da campanha"""
    if not stellar_service:
        raise HTTPException(status_code=500, detail="Serviço não disponível")
    
    try:
        stats = await stellar_service.get_campaign_stats()
        return {
            "total_raised": stats["total_raised"],
            "goal": CAMPAIGN_GOAL_XLM,
            "progress_percentage": stats["progress_percentage"],
            "is_active": stats["is_active"],
            "donations": stats["donations"],
            "donors_count": stats["donors_count"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar doações: {e}")

@app.get("/donations/top")
async def get_top_donors(limit: int = 10):
    """Retorna maiores doadores"""
    if not stellar_service:
        raise HTTPException(status_code=500, detail="Serviço não disponível")
    
    try:
        stats = await stellar_service.get_campaign_stats()
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
                    "first_donation": donation["timestamp"]
                }
        
        top_donors = sorted(donor_totals.values(), key=lambda x: x["total"], reverse=True)
        
        return {
            "top_donors": top_donors[:limit],
            "total_unique_donors": len(donor_totals)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar top doadores: {e}")

@app.get("/test/memo/{donor_name}/{amount}")
async def test_memo(donor_name: str, amount: float):
    """Testa formato do memo para uma doação"""
    memo = create_donation_memo(donor_name, amount)
    memo_bytes = len(memo.encode('ascii'))
    
    return {
        "donor_name": donor_name,
        "amount": amount,
        "memo": memo,
        "memo_bytes": memo_bytes,
        "is_valid": memo_bytes <= 28,
        "max_bytes": 28
    }

@app.get("/debug/account")
async def debug_account():
    """Informações de debug das contas"""
    if not stellar_service:
        return {"error": "Serviço não disponível"}
    
    try:
        campaign_account = server.load_account(stellar_service.campaign_keypair.public_key)
        
        donor_account = server.load_account(stellar_service.donor_keypair.public_key)
        
        return {
            "campaign_account": {
                "public_key": stellar_service.campaign_keypair.public_key,
                "balance": campaign_account.balances[0]["balance"] if campaign_account.balances else "0",
                "sequence": campaign_account.sequence
            },
            "donor_account": {
                "public_key": stellar_service.donor_keypair.public_key,
                "balance": donor_account.balances[0]["balance"] if donor_account.balances else "0",
                "sequence": donor_account.sequence
            },
            "campaign_config": {
                "title": CAMPAIGN_TITLE,
                "goal": CAMPAIGN_GOAL_XLM,
                "network": STELLAR_NETWORK
            }
        }
    except Exception as e:
        return {"error": f"Erro ao obter informações: {e}"}

@app.post("/simulate/donation/{count}")
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
        ("Lucia Costa", 20.0)
    ]
    
    results = []
    
    for i in range(min(count, len(fake_donations))):
        name, amount = fake_donations[i]
        
        try:
            stats = await stellar_service.get_campaign_stats()
            if not stats["is_active"]:
                break
            
            tx_hash = await stellar_service.process_donation(name, amount)
            results.append({
                "donor": name,
                "amount": amount,
                "hash": tx_hash,
                "success": True
            })
            
            import asyncio
            await asyncio.sleep(1)
            
        except Exception as e:
            results.append({
                "donor": name,
                "amount": amount,
                "error": str(e),
                "success": False
            })
    
    return {
        "simulated_donations": results,
        "message": f"{len([r for r in results if r['success']])} doações simuladas com sucesso"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)