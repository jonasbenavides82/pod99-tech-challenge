import os
import json
import boto3
from src.domain.entities import EventoTransacaoAutorizada
from src.application.ports import EventPublisher
from src.domain.exceptions import DomainError

class EventBridgePublisher(EventPublisher):
    def __init__(self):
        endpoint_url = os.getenv("EVENTBRIDGE_ENDPOINT_URL")
        self.client = boto3.client('events', endpoint_url=endpoint_url, region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.event_bus_name = os.getenv("EVENT_BUS_NAME", "pod99-event-bus")

    def publicar(self, evento: EventoTransacaoAutorizada) -> None:
        try:
            detail = {
                "event_id": evento.event_id,
                "event_type": evento.event_type,
                "event_version": evento.event_version,
                "occurred_at": evento.occurred_at,
                "id_autorizacao": evento.id_autorizacao,
                "id_contrato": evento.id_contrato,
                "valor": float(evento.valor),
                "saldo_reservado": float(evento.saldo_reservado),
                "correlation_id": evento.correlation_id
            }

            self.client.put_events(
                Entries=[
                    {
                        'Source': 'br.com.itau.pod99.autorizacao',
                        'DetailType': evento.event_type,
                        'Detail': json.dumps(detail),
                        'EventBusName': self.event_bus_name
                    }
                ]
            )
        except Exception as e:
            raise DomainError(f"Erro ao publicar evento: {e}")
