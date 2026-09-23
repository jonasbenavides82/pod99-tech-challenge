from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities import Contrato, EventoTransacaoAutorizada

class ContratoRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, id_contrato: str) -> Optional[Contrato]:
        pass

    @abstractmethod
    def salvar(self, contrato: Contrato) -> None:
        """
        Salva o contrato. Deve aplicar Optimistic Locking incrementando
        a versão e verificando concorrência.
        """
        pass

class EventPublisher(ABC):
    @abstractmethod
    def publicar(self, evento: EventoTransacaoAutorizada) -> None:
        pass
