# app/shared/exceptions.py
"""
Exceções Customizadas do Domínio

Este módulo define exceções específicas do negócio AgroKongo,
organizadas por domínio para facilitar tratamento granular de erros.

Princípios:
- Exceções específicas do domínio
- Mensagens claras para o utilizador
- Códigos de erro para integração
- Hierarquia de exceções
"""


# ============================================================
# Exceções Base
# ============================================================

class AgroKongoException(Exception):
    """Exceção base para todos os erros do domínio AgroKongo."""
    
    def __init__(self, message: str, code: str = "GENERIC_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


# ============================================================
# Exceções de Autenticação
# ============================================================

class AutenticacaoException(AgroKongoException):
    """Exceção base para erros de autenticação."""
    pass


class CredenciaisInvalidasException(AutenticacaoException):
    """Credenciais de login inválidas."""
    def __init__(self):
        super().__init__(
            message="Credenciais inválidas.",
            code="INVALID_CREDENTIALS"
        )


class UsuarioNaoEncontradoException(AutenticacaoException):
    """Utilizador não encontrado."""
    def __init__(self, identifier: str = None):
        msg = "Utilizador não encontrado."
        if identifier:
            msg = f"Utilizador com identificador '{identifier}' não encontrado."
        super().__init__(message=msg, code="USER_NOT_FOUND")


class ContaNaoValidadaException(AutenticacaoException):
    """Conta ainda não foi validada pelo administrador."""
    def __init__(self):
        super().__init__(
            message="A sua conta está pendente de validação.",
            code="ACCOUNT_NOT_VALIDATED"
        )


class SessaoExpiradaException(AutenticacaoException):
    """Sessão do utilizador expirou."""
    def __init__(self):
        super().__init__(
            message="A sua sessão expirou. Faça login novamente.",
            code="SESSION_EXPIRED"
        )


# ============================================================
# Exceções de Autorização
# ============================================================

class AutorizacaoException(AgroKongoException):
    """Exceção base para erros de autorização."""
    pass


class PermissaoNegadaException(AutorizacaoException):
    """Utilizador não tem permissão para executar ação."""
    def __init__(self, acao: str = None):
        msg = "Permissão negada."
        if acao:
            msg = f"Não tem permissão para executar: {acao}"
        super().__init__(message=msg, code="PERMISSION_DENIED")


class AcessoProibidoException(AutorizacaoException):
    """Acesso a recurso específico não permitido."""
    def __init__(self, recurso: str = None):
        msg = "Acesso proibido a este recurso."
        if recurso:
            msg = f"Acesso proibido ao recurso: {recurso}"
        super().__init__(message=msg, code="ACCESS_DENIED")


# ============================================================
# Exceções de Validação
# ============================================================

class ValidacaoException(AgroKongoException):
    """Exceção base para erros de validação."""
    pass


class DadosInvalidosException(ValidacaoException):
    """Dados fornecidos são inválidos."""
    def __init__(self, campo: str = None, motivo: str = None):
        msg = "Dados inválidos."
        if campo and motivo:
            msg = f"Campo '{campo}': {motivo}"
        elif campo:
            msg = f"Campo '{campo}' inválido."
        super().__init__(message=msg, code="INVALID_DATA")


class CampoObrigatorioException(ValidacaoException):
    """Campo obrigatório não fornecido."""
    def __init__(self, campo: str):
        super().__init__(
            message=f"Campo obrigatório não fornecido: {campo}",
            code="FIELD_REQUIRED"
        )


class FormatoInvalidoException(ValidacaoException):
    """Formato do dado não corresponde ao esperado."""
    def __init__(self, campo: str, formato_esperado: str):
        super().__init__(
            message=f"Campo '{campo}' com formato inválido. Esperado: {formato_esperado}",
            code="INVALID_FORMAT"
        )


# ============================================================
# Exceções de Transação (Escrow)
# ============================================================

class TransacaoException(AgroKongoException):
    """Exceção base para erros de transação."""
    pass


class TransacaoNaoEncontradaException(TransacaoException):
    """Transação não encontrada."""
    def __init__(self, transacao_id: int = None):
        msg = "Transação não encontrada."
        if transacao_id:
            msg = f"Transação #{transacao_id} não encontrada."
        super().__init__(message=msg, code="TRANSACTION_NOT_FOUND")


class TransacaoStatusInvalidoException(TransacaoException):
    """Status atual da transação não permite a operação."""
    def __init__(self, status_atual: str, operacao: str):
        super().__init__(
            message=f"Não é possível executar '{operacao}' com status '{status_atual}'.",
            code="INVALID_TRANSACTION_STATUS"
        )


class TransacaoJaExistenteException(TransacaoException):
    """Transação duplicada detectada."""
    def __init__(self, ref: str):
        super().__init__(
            message=f"Transação com referência '{ref}' já existe.",
            code="DUPLICATE_TRANSACTION"
        )


class SaldoInsuficienteException(TransacaoException):
    """Saldo insuficiente para operação."""
    def __init__(self, necessario: float, disponivel: float):
        super().__init__(
            message=f"Saldo insuficiente. Necessário: {necessario} Kz, Disponível: {disponivel} Kz",
            code="INSUFFICIENT_BALANCE"
        )


# ============================================================
# Exceções de Safra/Produto
# ============================================================

class SafraException(AgroKongoException):
    """Exceção base para erros relacionados a safras."""
    pass


class SafraNaoEncontradaException(SafraException):
    """Safra não encontrada."""
    def __init__(self, safra_id: int = None):
        msg = "Safra não encontrada."
        if safra_id:
            msg = f"Safra #{safra_id} não encontrada."
        super().__init__(message=msg, code="HARVEST_NOT_FOUND")


class QuantidadeInsuficienteException(SafraException):
    """Quantidade solicitada excede disponível."""
    def __init__(self, disponivel: float, solicitado: float):
        super().__init__(
            message=f"Quantidade insuficiente. Disponível: {disponivel} kg, Solicitado: {solicitado} kg",
            code="INSUFFICIENT_QUANTITY"
        )


class ProdutoNaoEncontradoException(SafraException):
    """Produto não encontrado."""
    def __init__(self, produto_id: int = None, nome: str = None):
        msg = "Produto não encontrado."
        if produto_id:
            msg = f"Produto #{produto_id} não encontrado."
        elif nome:
            msg = f"Produto '{nome}' não encontrado."
        super().__init__(message=msg, code="PRODUCT_NOT_FOUND")


# ============================================================
# Exceções de Infraestrutura
# ============================================================

class InfraestruturaException(AgroKongoException):
    """Exceção base para erros de infraestrutura."""
    pass


class DatabaseException(InfraestruturaException):
    """Erro na base de dados."""
    def __init__(self, detalhes: str = None):
        msg = "Erro na base de dados."
        if detalhes:
            msg = f"Erro na base de dados: {detalhes}"
        super().__init__(message=msg, code="DATABASE_ERROR")


class StorageException(InfraestruturaException):
    """Erro no armazenamento de ficheiros."""
    def __init__(self, detalhes: str = None):
        msg = "Erro no armazenamento."
        if detalhes:
            msg = f"Erro no armazenamento: {detalhes}"
        super().__init__(message=msg, code="STORAGE_ERROR")


class ServicoExternoException(InfraestruturaException):
    """Erro em serviço externo."""
    def __init__(self, servico: str, detalhes: str = None):
        msg = f"Erro no serviço externo: {servico}."
        if detalhes:
            msg += f" Detalhes: {detalhes}"
        super().__init__(message=msg, code="EXTERNAL_SERVICE_ERROR")


# ============================================================
# Exceções de Conformidade (LGPD)
# ============================================================

class ConformidadeException(AgroKongoException):
    """Exceção base para erros de conformidade."""
    pass


class ConsentimentoObrigatorioException(ConformidadeException):
    """Consentimento do utilizador é obrigatório."""
    def __init__(self, tipo_consentimento: str):
        super().__init__(
            message=f"Consentimento '{tipo_consentimento}' é obrigatório.",
            code="CONSENT_REQUIRED"
        )


class DadosPessoaisException(ConformidadeException):
    """Erro no processamento de dados pessoais."""
    def __init__(self, operacao: str):
        super().__init__(
            message=f"Erro ao processar dados pessoais: {operacao}",
            code="PERSONAL_DATA_ERROR"
        )


# ============================================================
# Factories para criação de exceções
# ============================================================

def criar_excecao_validacao(campo: str, erro: str) -> ValidacaoException:
    """Factory para criar exceção de validação."""
    return DadosInvalidosException(campo=campo, motivo=erro)


def criar_excecao_autenticacao(tipo: str) -> AutenticacaoException:
    """Factory para criar exceção de autenticação."""
    factories = {
        'credenciais': CredenciaisInvalidasException(),
        'nao_encontrado': UsuarioNaoEncontradoException(),
        'nao_validado': ContaNaoValidadaException(),
        'sessao_expirada': SessaoExpiradaException(),
    }
    return factories.get(tipo, CredenciaisInvalidasException())
