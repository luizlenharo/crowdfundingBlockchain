from typing import Dict

from app.config import settings
from app.utils.helpers import create_donation_memo
from stellar_sdk import Asset, Keypair, Server, TransactionBuilder


class StellarCrowdfundingService:
    def __init__(self):
        if not settings.CAMPAIGN_ACCOUNT_SECRET:
            raise ValueError("CAMPAIGN_ACCOUNT_SECRET não configurado")
        if not settings.DONOR_ACCOUNT_SECRET:
            raise ValueError("DONOR_ACCOUNT_SECRET não configurado")

        try:
            self.server = Server(settings.HORIZON_URL)
            self.campaign_keypair = Keypair.from_secret(
                settings.CAMPAIGN_ACCOUNT_SECRET
            )
            self.donor_keypair = Keypair.from_secret(settings.DONOR_ACCOUNT_SECRET)

            print(f"(Success) Campanha configurada: {self.campaign_keypair.public_key}")
            print(
                f"(Success) Conta doador configurada: {self.donor_keypair.public_key}"
            )

        except Exception as e:
            raise ValueError(f"Erro nas chaves Stellar: {e}")

    async def process_donation(self, donor_name: str, amount: float) -> str:
        """Processa doação na blockchain Stellar"""
        try:
            donor_account = self.server.load_account(self.donor_keypair.public_key)

            memo_text = create_donation_memo(donor_name, amount)

            transaction = (
                TransactionBuilder(
                    source_account=donor_account,
                    network_passphrase=settings.NETWORK_PASSPHRASE,
                    base_fee=100,
                )
                .add_text_memo(memo_text)
                .append_payment_op(
                    destination=self.campaign_keypair.public_key,
                    amount=str(amount),
                    asset=Asset.native(),
                )
                .set_timeout(30)
                .build()
            )

            transaction.sign(self.donor_keypair)
            response = self.server.submit_transaction(transaction)

            return response["hash"]

        except Exception as e:
            raise Exception(f"Erro na transação Stellar: {str(e)}")

    async def get_campaign_stats(self) -> Dict:
        """Calcula estatísticas da campanha baseado na blockchain"""
        try:
            transactions = (
                self.server.transactions()
                .for_account(self.campaign_keypair.public_key)
                .limit(200)
                .order(desc=True)
                .call()
            )

            total_raised = 0.0
            donations = []

            for tx in transactions["_embedded"]["records"]:
                try:
                    operations = (
                        self.server.operations().for_transaction(tx["hash"]).call()
                    )

                    for op in operations["_embedded"]["records"]:
                        if (
                            op["type"] == "payment"
                            and op["to"] == self.campaign_keypair.public_key
                            and op["asset_type"] == "native"
                        ):
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

                            donations.append(
                                {
                                    "donor_name": donor_name,
                                    "amount": amount,
                                    "transaction_hash": tx["hash"],
                                    "timestamp": tx["created_at"],
                                    "memo": memo,
                                }
                            )

                except Exception as e:
                    print(f"Erro ao processar operação: {e}")
                    continue

            progress = min((total_raised / settings.CAMPAIGN_GOAL_XLM) * 100, 100)
            is_active = total_raised < settings.CAMPAIGN_GOAL_XLM

            return {
                "total_raised": total_raised,
                "goal": settings.CAMPAIGN_GOAL_XLM,
                "progress_percentage": progress,
                "is_active": is_active,
                "donations": sorted(
                    donations, key=lambda x: x["timestamp"], reverse=True
                ),
                "donors_count": len(donations),
            }

        except Exception as e:
            print(f"Erro ao calcular estatísticas: {e}")
            return {
                "total_raised": 0.0,
                "goal": settings.CAMPAIGN_GOAL_XLM,
                "progress_percentage": 0.0,
                "is_active": True,
                "donations": [],
                "donors_count": 0,
            }

    def get_account_info(self, public_key: str) -> Dict:
        """Retorna informações de uma conta Stellar"""
        try:
            account = self.server.load_account(public_key)
            return {
                "public_key": public_key,
                "balance": account.balances[0]["balance"] if account.balances else "0",
                "sequence": account.sequence,
            }
        except Exception as e:
            return {"error": f"Erro ao carregar conta: {e}"}
