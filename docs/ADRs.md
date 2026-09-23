# Architecture Decision Records (ADRs)

## ADR 1: Uso de DynamoDB com Optimistic Locking em vez de RDBMS
**Contexto**: A plataforma precisa lidar com picos de 5.000 TPS de autorização, com garantia de integridade do limite reservado.
**Decisão**: Escolhemos o Amazon DynamoDB para persistência. Para evitar condições de corrida na reserva de limites, utilizamos o padrão de *Optimistic Locking* (versão) no `put_item` através do `ConditionExpression`.
**Consequências**:
- Altíssima escalabilidade e latência previsível (single-digit ms).
- Caso ocorra colisão, a requisição lançará um erro HTTP 409 (Conflict), forçando o cliente a tentar novamente.

## ADR 2: Uso de AWS Lambda via API Gateway vs ECS Fargate
**Contexto**: A API síncrona de autorização deve suportar tráfego intermitente e picos súbitos (Black Friday, início do mês).
**Decisão**: Utilizamos AWS Lambda exposta via API Gateway REST API. O código foi implementado em Python utilizando FastAPI e Mangum como adapter.
**Consequências**:
- Menor custo operacional em períodos de baixa, com *scale-out* imediato.
- Padrão *contract-first* é facilitado pelo OpenAPI nativo do FastAPI.
- Desvantagem: Possibilidade de *Cold Starts*, que podem ser mitigados usando Provisioned Concurrency para garantir SLAs de latência.

## ADR 3: Idempotência via Header e Idempotency-Key
**Contexto**: O contrato exige que as requisições possuam o header `Idempotency-Key` com um UUID.
**Decisão**: A idempotência deve ser delegada para a borda da aplicação (Camada de Infra/Adapter) utilizando a utilidade de Idempotency do AWS Lambda Powertools.
**Consequências**:
- Desacopla o domínio da lógica técnica de idempotência.
- Evita duplo débito no limite do contrato, preservando a consistência financeira.

## ADR 4: Event-Driven Architecture (Amazon EventBridge)
**Contexto**: Após autorizada, a transação deve ser notificada para sistemas desacoplados (fraude, contabilidade).
**Decisão**: Utilizamos o Amazon EventBridge para receber e rotear os eventos de domínio (`TransacaoAutorizada`).
**Consequências**:
- Desacoplamento nativo com múltiplos targets.
- O EventBridge não garante ordenação restrita como o Kafka, porém o requisito foca em entrega e desacoplamento. Caso a ordenação seja estritamente necessária por conta, poderia ser substituído por Kinesis Data Streams (via partition key `id_conta`).
