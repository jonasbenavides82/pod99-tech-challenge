# Arquitetura da Solução

Abaixo apresentamos o desenho arquitetural da Plataforma de Autorização desenhada para a AWS usando Serverless.

```mermaid
flowchart TD
    %% Atores
    Client(Cliente / Canal)
    
    %% Borda AWS
    subgraph AWS [AWS Cloud]
        API_GW[Amazon API Gateway\nThrottling / Rate Limit]
        
        %% Computação
        Lambda[AWS Lambda\nFastAPI - Autorizador]
        
        %% Persistência
        DynamoDB[(Amazon DynamoDB\nTabela: Contratos\nOptimistic Locking)]
        
        %% Mensageria
        EventBridge((Amazon EventBridge\nEvent Bus))
    end
    
    %% Consumidores Desacoplados
    subgraph Consumidores [Sistemas de Retaguarda]
        Fraude[Prevenção a Fraude]
        Contabilidade[Contabilidade]
        DataPlatform[Data Platform]
    end

    %% Fluxo
    Client -- "1. POST /v1/contratos/{id}/autorizacoes\nIdempotency-Key" --> API_GW
    API_GW -- "2. Invoca" --> Lambda
    Lambda -- "3. Valida Limite & Reserva (Locking)" --> DynamoDB
    Lambda -- "4. Retorna (201 Created)" --> API_GW
    API_GW -- "5. Retorna (201 Created)" --> Client
    
    Lambda -- "6. Publica Evento (TransacaoAutorizada)" --> EventBridge
    
    EventBridge -- "Push" --> Fraude
    EventBridge -- "Push" --> Contabilidade
    EventBridge -- "Push" --> DataPlatform

    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:white;
    classDef lambda fill:#D18B17,stroke:#232F3E,stroke-width:2px,color:white;
    classDef dynamo fill:#3B48CC,stroke:#232F3E,stroke-width:2px,color:white;
    classDef ext fill:#8B8C8A,stroke:#333,stroke-width:2px,color:white;
    classDef eventbus fill:#FF4F8B,stroke:#232F3E,stroke-width:2px,color:white;
    
    class API_GW aws;
    class Lambda lambda;
    class DynamoDB dynamo;
    class EventBridge eventbus;
    class Fraude,Contabilidade,DataPlatform ext;
```

## Como a arquitetura atende aos requisitos funcionais e não-funcionais:
1. **Volumetria (5.000 TPS)**: O AWS Lambda e API Gateway escalam automaticamente para suportar picos bruscos sem necessitar de pré-provisionamento. O DynamoDB entrega latências na casa de milissegundos para escrita e leitura independente do volume.
2. **Consistência de Dados**: Evitamos o débito duplo usando o *Optimistic Locking* diretamente nas chamadas do SDK (`ConditionExpression` checando a versão do contrato).
3. **Desacoplamento**: O sistema processa o crédito, atualiza o limite síncronamente e propaga a notificação usando EventBridge para que outros serviços internos se virem, mantendo a latência da API focada na autorização.
