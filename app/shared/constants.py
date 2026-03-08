"""
Constantes globais do AgroKongo
Centraliza todas as constantes e configurações do sistema
"""

# ==================== CADASTRO ====================
CADASTRO_SENHA_MIN_DIGITOS = 4
CADASTRO_SENHA_MAX_DIGITOS = 6
CADASTRO_OTP_TAMANHO = 6
CADASTRO_OTP_VALIDADE_MINUTOS = 10
CADASTRO_OTP_MAX_TENTATIVAS = 3
CADASTRO_REENVIO_COOLDOWN_SEGUNDOS = 60

# ==================== VALIDAÇÕES ====================
TELEMOVEL_PREFIXO = '9'
TELEMOVEL_TAMANHO = 9
IBAN_PREFIXO = 'AO06'
IBAN_TAMANHO = 27
IBAN_PAIS = 'AO'

# ==================== UPLOAD ====================
UPLOAD_TAMANHO_MAXIMO_MB = 5
UPLOAD_FORMATOS_PERMITIDOS_IMAGEM = {'jpg', 'jpeg', 'png', 'webp'}
UPLOAD_FORMATOS_PERMITIDOS_DOCUMENTO = {'pdf', 'jpg', 'jpeg', 'png'}
UPLOAD_QUALIDADE_WEBP = 85

# ==================== PAGINAÇÃO ====================
PAGINACAO_PADRAO = 10
PAGINACAO_MAXIMO = 100

# ==================== TRANSAÇÕES ====================
TRANSCAO_COMISSAO_PLATAFORMA_PERCENTUAL = 5.0
TRANSCAO_TEMPO_ANALISE_HORAS = 24
TRANSCAO_TEMPO_ENVIO_HORAS = 72
TRANSCAO_STATUS = {
    'PENDENTE': 'pendente',
    'ANALISE': 'analise',
    'ESCROW': 'escrow',
    'ENVIADO': 'enviado',
    'ENTREGUE': 'entregue',
    'FINALIZADO': 'finalizado',
    'CANCELADO': 'cancelado'
}

# ==================== SEGURANÇA ====================
SEGURANCA_TOKEN_EXPIRACAO_HORAS = 24
SEGURANCA_MAX_LOGIN_TENTATIVAS = 5
SEGURANCA_LOCKOUT_MINUTOS = 30
SEGURANCA_SALT_ROUNDS = 12

# ==================== NOTIFICAÇÕES ====================
NOTIFICACAO_MAX_LIDAS_POR_VEZ = 50
NOTIFICACAO_RETENCIÃO_DIAS = 90

# ==================== FINANCEIRO ====================
FINANCEIRO_VALOR_MINIMO_KZ = 100.00
FINANCEIRO_VALOR_MAXIMO_KZ = 10000000.00
FINANCEIRO_DECIMAIS_PRECISAO = 2

# ==================== API ====================
API_RATE_LIMIT_POR_MINUTO = 60
API_TIMEOUT_SEGUNDOS = 30
API_VERSION = 'v1'

# ==================== ARQUITETURA ====================
AMBIENTE = {
    'DESENVOLVIMENTO': 'development',
    'TESTE': 'testing',
    'PRODUCAO': 'production',
    'STAGING': 'staging'
}

# ==================== ERROS ====================
ERRO_MENSAGENS = {
    'NAO_AUTORIZADO': 'Acesso não autorizado',
    'RECURSO_NAO_ENCONTRADO': 'Recurso não encontrado',
    'DADOS_INVALIDOS': 'Dados inválidos',
    'ERRO_INTERNO': 'Erro interno do servidor',
    'MANUTENCAO': 'Sistema em manutenção'
}

# ==================== AUDITORIA ====================
AUDITORIA_ACOES = {
    'LOGIN': 'LOGIN',
    'LOGOUT': 'LOGOUT',
    'CADASTRO_PRODUTOR': 'CADASTRO_PRODUTOR',
    'CRIAR_SAFRA': 'CRIAR_SAFRA',
    'EDITAR_SAFRA': 'EDITAR_SAFRA',
    'ELIMINAR_SAFRA': 'ELIMINAR_SAFRA',
    'CRIAR_TRANSACAO': 'CRIAR_TRANSACAO',
    'CANCELAR_TRANSACAO': 'CANCELAR_TRANSACAO',
    'FINALIZAR_TRANSACAO': 'FINALIZAR_TRANSACAO',
    'UPLOAD_DOCUMENTO': 'UPLOAD_DOCUMENTO',
    'ALTERAR_SENHA': 'ALTERAR_SENHA',
    'CONFIRMACAO_RECEBIMENTO': 'CONFIRMACAO_RECEBIMENTO',
    'ABERTURA_DISPUTA': 'ABERTURA_DISPUTA',
    'AVALIACAO_VENDA': 'AVALIACAO_VENDA'
}
