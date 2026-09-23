# POD99 - Tech Challenge: Plataforma de Gestão de Limites e Autorização

Projeto de microsserviço Serverless (Python/FastAPI) em Clean Architecture para o desafio técnico do Itaú.

## Requisitos
- Docker e docker-compose
- Python 3.11+ (para execução local dos testes)
- Terraform (Opcional, para testes do IaC)

## Como executar localmente
A aplicação foi projetada para usar o LocalStack e simular o DynamoDB e o EventBridge localmente.

1. Suba a stack (API e LocalStack):
   ```bash
   docker-compose up --build -d
   ```

2. Provisione os recursos no LocalStack via Terraform (em outro terminal):
   ```bash
   cd infra
   terraform init
   terraform apply -auto-approve
   ```

3. Acesse o Swagger UI (OpenAPI):
   [http://localhost:8000/docs](http://localhost:8000/docs)

4. Rode os testes unitários (opcional):
   ```bash
   pip install -r requirements.txt
   pytest tests/
   ```

## Testando a API

### Criar Contrato Fake no Banco
Como estamos usando LocalStack, precisamos inserir um contrato para testar:
```bash
aws dynamodb put-item \
    --endpoint-url http://localhost:4566 \
    --table-name Contratos \
    --item '{"id_contrato": {"S": "CONTRATO#123"}, "id_conta": {"S": "abc"}, "limite_total": {"N": "1000"}, "limite_disponivel": {"N": "1000"}, "versao": {"N": "1"}}'
```

### Realizar Autorização
```bash
curl -X POST http://localhost:8000/v1/contratos/123/autorizacoes \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: f342-990a-1123" \
  -d '{
    "id_conta": "abc",
    "valor": 150.00,
    "moeda": "BRL",
    "tipo_operacao": "CREDITO"
  }'
```
