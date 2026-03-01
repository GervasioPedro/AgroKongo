# app/tasks/pagamentos.py - Versão auditada, atômica e auditável (produção-ready)
# Versão Corrigida - 26/02/2026
from celery import shared_task
from flask import url_for
from app.extensions import db, current_app
from app.tasks.base import AgroKongoTask
from app.models import (
    Transacao, TransactionStatus, PagamentoLog, Notificacao,
    LogAuditoria, Usuario, MovimentacaoFinanceira
)
from app.utils.helpers import aware_utcnow
from sqlalchemy.orm import joinedload


@shared_task(bind=True, base=AgroKongoTask, max_retries=5, rate_limit='5/m')
def processar_liquidacao(self, trans_id: int):
    """
    Liquidação async segura (ENTREGUE → FINALIZADO + saldo vendedor).
    Segurança: lock, validação, logs duplos, atomicidade.
    UX: notificações ambos lados com valores/data.
    """
    try:
        transacao = db.session.query(Transacao).options(
            joinedload(Transacao.vendedor),
            joinedload(Transacao.comprador)
        ).with_for_update().get(trans_id)

        if not transacao:
            raise ValueError(f"Transação {trans_id} não encontrada.")

        if transacao.status != TransactionStatus.ENTREGUE or transacao.transferencia_concluida:
            raise ValueError(
                f"Transação {trans_id} inválida para liquidação (status: {transacao.status})."
            )

        # Atualizações financeiras
        transacao.transferencia_concluida = True
        transacao.status = TransactionStatus.FINALIZADO
        transacao.data_liquidacao = aware_utcnow()

        # ✅ Criar movimentação financeira em vez de atribuir saldo
        movimentacao = MovimentacaoFinanceira(
            usuario_id=transacao.vendedor_id,
            transacao_id=transacao.id,
            valor=transacao.valor_liquido_vendedor,
            tipo='credito_liquidacao',
            descricao=f"Liquidação venda {transacao.fatura_ref}"
        )
        db.session.add(movimentacao)

        # Atualizar contador de vendas
        transacao.vendedor.vendas_concluidas = (transacao.vendedor.vendas_concluidas or 0) + 1

        # Notificações ambos (UX completa)
        db.session.add(Notificacao(
            usuario_id=transacao.vendedor_id,
            mensagem=f"💰 Liquidação concluída! +{float(transacao.valor_liquido_vendedor):.2f} Kz na transação {transacao.fatura_ref}.",
            link="/produtor/dashboard"
        ))

        db.session.add(Notificacao(
            usuario_id=transacao.comprador_id,
            mensagem=f"✅ Transação {transacao.fatura_ref} finalizada com sucesso! Obrigado pela confiança.",
            link="/comprador/minhas-compras"
        ))

        # Logs auditoria dupla
        db.session.add(PagamentoLog(
            trans_id=transacao.fatura_ref,
            valor_liquidado=transacao.valor_liquido_vendedor,
            acao="LIQUIDACAO_SUCCESS",
            detalhes=f"Liquidado para vendedor {transacao.vendedor_id} (task {self.request.id})",
            data=aware_utcnow()
        ))

        db.session.add(LogAuditoria(
            usuario_id=None,  # System
            acao="LIQUIDACAO_FINANCEIRA",
            detalhes=f"Transação {transacao.fatura_ref} liquidada: +{float(transacao.valor_liquido_vendedor):.2f} Kz ao vendedor {transacao.vendedor_id}",
            ip="celery_task"
        ))

        db.session.commit()
        current_app.logger.info(f"✅ Liquidação {transacao.fatura_ref} concluída")

    except ValueError as ve:
        current_app.logger.warning(f"Erro lógico liquidação {trans_id}: {ve}")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro task liquidação {trans_id}: {e}", exc_info=True)
        raise self.retry(exc=e)

    return "Liquidação concluída"


@shared_task(bind=True, base=AgroKongoTask, max_retries=3, rate_limit='10/d')
def enviar_lembretes_pendentes(self):
    """
    Envia lembretes de pagamento pendente (task agendada 9:00 AM diariamente).
    """
    try:
        # Transações pendentes há mais de 24h
        limite = aware_utcnow() - timezone.timedelta(hours=24)

        transacoes_pendentes = Transacao.query.filter(
            Transacao.status == TransactionStatus.AGUARDANDO_PAGAMENTO,
            Transacao.data_criacao <= limite
        ).all()

        for t in transacoes_pendentes:
            db.session.add(Notificacao(
                usuario_id=t.comprador_id,
                mensagem=f"⏰ Lembrete: Sua reserva {t.fatura_ref} aguarda pagamento há mais de 24h. Complete para não perder o stock!",
                link=f"/comprador/submeter-comprovativo/{t.id}"
            ))

        db.session.commit()
        current_app.logger.info(f"✅ {len(transacoes_pendentes)} lembretes de pagamento enviados")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro task lembretes: {e}", exc_info=True)
        raise self.retry(exc=e)

    return "Lembretes enviados"


# ==================== IMPORTS ====================
from datetime import timezone