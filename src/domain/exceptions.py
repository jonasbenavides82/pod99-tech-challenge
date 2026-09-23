class DomainError(Exception):
    """Base class for all domain exceptions."""
    pass

class LimiteInsuficienteError(DomainError):
    """Exception raised when an account limit is insufficient."""
    pass

class ContratoNaoEncontradoError(DomainError):
    """Exception raised when a contract is not found."""
    pass
