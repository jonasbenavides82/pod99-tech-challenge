import os
import boto3
from decimal import Decimal
from typing import Optional
from botocore.exceptions import ClientError

from src.domain.entities import Contrato
from src.application.ports import ContratoRepository
from src.domain.exceptions import DomainError

class DynamoDBContratoRepository(ContratoRepository):
    def __init__(self):
        # Allow overriding endpoint for LocalStack
        endpoint_url = os.getenv("DYNAMODB_ENDPOINT_URL")
        self.dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url, region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.table_name = os.getenv("CONTRATOS_TABLE", "Contratos")
        self.table = self.dynamodb.Table(self.table_name)

    def buscar_por_id(self, id_contrato: str) -> Optional[Contrato]:
        try:
            response = self.table.get_item(
                Key={'id_contrato': f"CONTRATO#{id_contrato}"}
            )
            item = response.get('Item')
            if not item:
                return None
            
            return Contrato(
                id_contrato=id_contrato,
                id_conta=item.get('id_conta'),
                limite_total=Decimal(str(item.get('limite_total'))),
                limite_disponivel=Decimal(str(item.get('limite_disponivel'))),
                versao=int(item.get('versao', 1))
            )
        except ClientError as e:
            raise DomainError(f"Erro ao acessar DynamoDB: {e}")

    def salvar(self, contrato: Contrato) -> None:
        nova_versao = contrato.versao + 1
        try:
            self.table.put_item(
                Item={
                    'id_contrato': f"CONTRATO#{contrato.id_contrato}",
                    'id_conta': contrato.id_conta,
                    'limite_total': contrato.limite_total,
                    'limite_disponivel': contrato.limite_disponivel,
                    'versao': nova_versao
                },
                ConditionExpression="attribute_not_exists(versao) OR versao = :versao_atual",
                ExpressionAttributeValues={
                    ":versao_atual": contrato.versao
                }
            )
            contrato.versao = nova_versao
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise DomainError("Conflito de concorrência ao atualizar o contrato")
            raise DomainError(f"Erro ao salvar no DynamoDB: {e}")
