from datetime import datetime, timedelta, timezone
from app.models import Transacao, TransactionStatus, Notificacao, Safra
from app.extensions import db


def monitorar_transacoes_estagnadas():
    """
    Motor de integridade do AgroKongo:
    1. Notifica Admins sobre atrasos na validação.
    2. Liberta stock de reservas não pagas (Auto-Cancelamento).
    """
    agora = datetime.now(timezone.utc)
    limite_analise = agora - timedelta(hours=24)
    limite_expiracao = agora - timedelta(hours=48)

    # --- 1. AUDITORIA INTERNA (Admin) ---
    estagnadas_admin = Transacao.query.filter(
        Transacao.status == TransactionStatus.ANALISE,
        Transacao.data_criacao <= limite_analise
    ).all()

    for t in estagnadas_admin:
        # Aqui apenas logamos. O Admin verá isso no dashboard de 'Alertas'
        print(f"⚠️ ADMIN_DELAY: {t.fatura_ref} pendente de validação há +24h.")

    # --- 2. GESTÃO DE STOCK E CANCELAMENTO (Comprador) ---
    reservas_expiradas = Transacao.query.filter(
        Transacao.status == TransactionStatus.PENDENTE,
        Transacao.data_criacao <= limite_expiracao
    ).all()

    canceladas_count = 0
    for t in reservas_expiradas:
        try:
            # A. Devolver o stock ao produtor
            safra = Safra.query.get(t.safra_id)
            if safra:
                safra.quantidade_disponivel += t.quantidade_comprada
                if safra.status == 'esgotado':
                    safra.status = 'disponivel'

            # B. Mudar status da transação
            t.status = TransactionStatus.CANCELADO

            # C. Notificar o comprador do cancelamento
            aviso = Notificacao(
                usuario_id=t.comprador_id,
                mensagem=f"A sua reserva {t.fatura_ref} expirou por falta de pagamento. O stock foi devolvido ao produtor.",
                link="/mercado"  # Redireciona para ele comprar de novo se quiser
            )
            db.session.add(aviso)
            canceladas_count += 1

        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao cancelar transação {t.id}: {e}")

    db.session.commit()
    if canceladas_count > 0:
        print(f"♻️ Limpeza Concluída: {canceladas_count} reservas canceladas e stock libertado.")