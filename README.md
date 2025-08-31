# Projeto Blockchain

## Descrição do Projeto

Sistema de vaquinha (crowdfunding) descentralizada que utiliza a blockchain Stellar para registrar doações de forma transparente e imutável. O organizador define uma meta em XLM, e as pessoas podem doar até que a meta seja atingida. Cada doação é registrada na blockchain com o nome do doador e valor.

## Objetivo

Demonstrar uso avançado da blockchain Stellar para gerenciamento de fundos coletivos, com transparência total e impossibilidade de manipulação dos valores arrecadados.

## Arquitetura

### Frontend (Vue.js)
- Interface para criar campanhas
- Dashboard para doações
- Progresso visual da meta
- Lista de doadores em tempo real

### Backend (FastAPI)
- API para gerenciar campanhas
- Processamento de doações via Stellar
- Cálculo automático do progresso
- Validação de metas atingidas

### Blockchain Integration
- **Rede**: Stellar Testnet
- **Conta Campanha**: Recebe todas as doações
- **Memos**: Nome do doador + informações da doação
- **Valor**: Quantia real doada em XLM

## Como executar

### 1. Instalar as dependências

Navegue até o diretório do backend e instale as dependências:

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configurar o blockchain

Execute o script de configuração:

```bash
python ./setup.py
```

### 3. Executar o backend

Inicie o servidor backend com uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Executar o frontend

Em um novo terminal, navegue até o diretório do frontend e inicie o servidor:

```bash
cd frontend
python -m http.server 3000
```

## Acesso

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000

## Estrutura do projeto

```
.
├── README.md
├── backend
│   ├── __pycache__
│   │   ├── main.cpython-312.pyc
│   │   └── main.cpython-313.pyc
│   ├── app
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── models
│   │   │   └── schemas.py
│   │   ├── routes
│   │   │   ├── campaign.py
│   │   │   ├── debug.py
│   │   │   └── donations.py
│   │   ├── services
│   │   │   └── stellarService.py
│   │   └── utils
│   │       └── helpers.py
│   └── requirements.txt
└── frontend
    ├── index.html
    └── package.json
```

## Observações

- Certifique-se de ter Python instalado em sua máquina
- O backend será executado na porta 8000
- O frontend será executado na porta 3000
- Use `--reload` no uvicorn para desenvolvimento (recarregamento automático)
