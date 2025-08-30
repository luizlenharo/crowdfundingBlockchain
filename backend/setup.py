"""
Configurador de Campanha para o Sistema de Vaquinha Stellar
"""

from stellar_sdk import Keypair
import requests
import time

def create_keypair():
    """Cria um novo par de chaves Stellar"""
    kp = Keypair.random()
    return {
        'public_key': kp.public_key,
        'secret_key': kp.secret
    }

def fund_account(public_key):
    """Financia conta na testnet"""
    try:
        url = "https://friendbot.stellar.org"
        response = requests.get(url, params={'addr': public_key}, timeout=15)
        
        if response.status_code == 200:
            print(f"* Conta financiada: {public_key[:8]}...{public_key[-8:]}")
            return True
        else:
            print(f"X Erro no financiamento: {response.status_code}")
            return False
    except Exception as e:
        print(f"X Erro: {e}")
        return False

def get_campaign_details():
    """Coleta informações da campanha do usuário"""
    print("* Configuração da Campanha")
    print("-" * 40)
    
    title = input("Título da campanha: ").strip()
    if not title:
        title = "Vaquinha Comunitária"
    
    description = input("Descrição (opcional): ").strip()
    if not description:
        description = "Ajude nosso projeto!"
    
    while True:
        try:
            goal_input = input("Meta em XLM (ex: 100.0): ").strip()
            if not goal_input:
                goal = 100.0
                break
            goal = float(goal_input)
            if goal > 0:
                break
            else:
                print("Meta deve ser maior que 0")
        except ValueError:
            print("Digite um número válido")
    
    return {
        'title': title,
        'description': description,
        'goal': goal
    }

def create_env_file(campaign_keypair, donor_keypair, campaign_details):
    """Cria arquivo .env com todas as configurações"""
    
    env_content = f"""# Configurações da Rede Stellar
STELLAR_NETWORK=testnet

# Conta da Campanha (recebe as doações)
CAMPAIGN_ACCOUNT_SECRET={campaign_keypair['secret_key']}

# Conta Doador (envia as doações - simula doadores)
DONOR_ACCOUNT_SECRET={donor_keypair['secret_key']}

# Configurações da Campanha
CAMPAIGN_GOAL_XLM={campaign_details['goal']}
CAMPAIGN_TITLE={campaign_details['title']}
CAMPAIGN_DESCRIPTION={campaign_details['description']}"""
    
    with open('.env', 'w', encoding='utf-8', newline='\n') as f:
        f.write(env_content)
    
    print("(Success) Arquivo .env criado com sucesso!")

def main():
    print("Configurador de Campanha Stellar")
    print("=" * 50)
    
    if os.path.exists('.env'):
        response = input("Arquivo .env já existe. Recriar? (s/N): ")
        if response.lower() != 's':
            print("Configuração cancelada.")
            return
    
    campaign_details = get_campaign_details()
    
    print(f"* Configurando campanha: '{campaign_details['title']}'")
    print(f"* Meta: {campaign_details['goal']} XLM")
    
    print("\n1. Criando conta da campanha (urna)...")
    campaign_keypair = create_keypair()
    print(f"   Pública: {campaign_keypair['public_key']}")
    
    print("\n2. Criando conta doador (para simular doações)...")
    donor_keypair = create_keypair()
    print(f"   Pública: {donor_keypair['public_key']}")
    
    print("\n3. Financiando contas na testnet...")
    print("   (Isso pode demorar alguns segundos)")
    
    if fund_account(campaign_keypair['public_key']):
        time.sleep(2)
    
    if fund_account(donor_keypair['public_key']):
        time.sleep(1)
    
    print("\n4. Criando arquivo de configuração...")
    create_env_file(campaign_keypair, donor_keypair, campaign_details)
    
    print("\n(Success) Campanha configurada com sucesso!")
    
    print(f"\n* Resumo da Campanha:")
    print(f"Título: {campaign_details['title']}")
    print(f"Meta: {campaign_details['goal']} XLM")
    print(f"Conta da Campanha: {campaign_keypair['public_key']}")
    print(f"Conta Doador: {donor_keypair['public_key']}")
    
    print(f"\n* Links para verificação:")
    print(f"StellarExpert: https://stellar.expert/explorer/testnet/account/{campaign_keypair['public_key']}")
    
    print(f"\n* Próximos passos:")
    print("1. python -m uvicorn main:app --reload")
    print("2. Rode python -m http.server 3000")
    
    import json
    campaign_info = {
        'campaign_keypair': campaign_keypair,
        'donor_keypair': donor_keypair,
        'campaign_details': campaign_details,
        'created_at': datetime.now().isoformat(),
        'network': 'testnet'
    }
    
    with open('campaign_info.json', 'w', encoding='utf-8') as f:
        json.dump(campaign_info, f, indent=2, ensure_ascii=False)
    
    print("* Informações salvas em 'campaign_info.json'")

if __name__ == "__main__":
    import os
    from datetime import datetime
    main()