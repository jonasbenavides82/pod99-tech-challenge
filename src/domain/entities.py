import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from decimal import Decimal

@dataclass
class Contrato:
    """
    Representa a entidade de domínio de um Contrato Financeiro do cliente.
    
    Esta classe encapsula o estado do limite de crédito do cliente e aplica
    as regras de negócio primárias de autorização.
    
    Attributes:
        id_contrato (str): Identificador único do contrato.
        id_conta (str): Identificador da conta atrelada ao contrato.
        limite_total (Decimal): Limite de crédito total concedido.
        limite_disponivel (Decimal): Limite atual disponível para uso.
        versao (int): Controle de concorrência (Optimistic Locking).
    """
    id_contrato: str
    id_conta: str
    limite_total: Decimal
    limite_disponivel: Decimal
    versao: int

    def reservar_limite(self, valor: Decimal) -> None:
        """
        Reserva uma porção do limite disponível.
        
        Aplica as regras de negócio para garantir que o valor não seja
        negativo e que exista limite suficiente disponível antes de deduzir.

        Args:
            valor (Decimal): O valor monetário a ser reservado.

        Raises:
            ValueError: Se o valor da transação for zero ou negativo.
            LimiteInsuficienteError: Se o valor exceder o limite disponível.
        """
        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero")
        if self.limite_disponivel < valor:
            from .exceptions import LimiteInsuficienteError
            raise LimiteInsuficienteError(f"Limite insuficiente para o contrato {self.id_contrato}")
        
        self.limite_disponivel -= valor

@dataclass
class Transacao:
    """
    Representa uma transação de autorização solicitada pelo canal.
    
    Attributes:
        id_transacao (str): UUID único da transação gerado pelo domínio.
        id_contrato (str): Identificador do contrato sendo debitado.
        id_conta (str): Identificador da conta.
        valor (Decimal): Valor monetário solicitado.
        moeda (str): Moeda da transação (ex: BRL).
        tipo_operacao (str): Tipo da operação (ex: CREDITO).
        id_estabelecimento (str): Código do estabelecimento solicitante.
        metadata (dict): Dados adicionais arbitrários da transação.
        data_hora (datetime): Timestamp do momento da autorização.
    """
    id_transacao: str
    id_contrato: str
    id_conta: str
    valor: Decimal
    moeda: str
    tipo_operacao: str
    id_estabelecimento: str
    metadata: dict
    data_hora: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class EventoTransacaoAutorizada:
    """
    Evento de domínio publicado após o sucesso da autorização.
    
    Este DTO é serializado e enviado ao Amazon EventBridge para
    desacoplar a notificação a sistemas consumidores (ex: Fraude).
    """
    event_id: str
    event_type: str
    event_version: str
    occurred_at: str
    id_autorizacao: str
    id_contrato: str
    valor: Decimal
    saldo_reservado: Decimal
    correlation_id: str
