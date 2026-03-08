"""
Base models - Helpers e mixins comuns
"""
from datetime import datetime, timezone
from app.extensions import db


def aware_utcnow():
    """Helper para consistência de tempo em servidores globais"""
    return datetime.now(timezone.utc)


class TransactionStatus:
    """Constantes de status de transação"""
    PENDENTE = 'pendente'
    AGUARDANDO_PAGAMENTO = 'pendente_pagamento'
    ANALISE = 'pagamento_sob_analise'
    ESCROW = 'pago_escrow'
    ENVIADO = 'mercadoria_enviada'
    ENTREGUE = 'mercadoria_entregue'
    FINALIZADO = 'finalizada'
    CANCELADO = 'cancelada'
    DISPUTA = 'em_disputa'


class StatusConta:
    """Status da conta do usuário"""
    PENDENTE_VERIFICACAO = 'PENDENTE_VERIFICACAO'
    VERIFICADO = 'VERIFICADO'
    REJEITADO = 'REJEITADO'
    SUSPENSO = 'SUSPENSO'
    
    @classmethod
    def choices(cls):
        """Retorna lista de choices para formulários"""
        return [
            (cls.PENDENTE_VERIFICACAO, 'Pendente Verificação'),
            (cls.VERIFICADO, 'Verificado'),
            (cls.REJEITADO, 'Rejeitado'),
            (cls.SUSPENSO, 'Suspenso')
        ]
    
    @classmethod
    def is_valid(cls, valor):
        """Valida se o valor é um status válido"""
        return valor in [cls.PENDENTE_VERIFICACAO, cls.VERIFICADO, cls.REJEITADO, cls.SUSPENSO]
