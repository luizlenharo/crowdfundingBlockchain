# Projeto Blockchain

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
./
├── app/
│   ├── __init__.py
│   ├── main.py              # Ponto de entrada principal
│   ├── config.py            # Configurações
│   ├── models/              # Modelos de dados
│   │   ├── __init__.py
│   │   └── user.py
│   ├── routes/              # Rotas/endpoints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── api.py
│   ├── services/            # Lógica de negócio
│   │   ├── __init__.py
│   │   └── user_service.py
│   └── utils/               # Funções auxiliares
│       ├── __init__.py
│       └── helpers.py
├── tests/
├── requirements.txt
└── README.md
```

## Observações

- Certifique-se de ter Python instalado em sua máquina
- O backend será executado na porta 8000
- O frontend será executado na porta 3000
- Use `--reload` no uvicorn para desenvolvimento (recarregamento automático)
