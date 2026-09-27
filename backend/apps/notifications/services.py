"""Serviços de notificação e pedidos de recuperação de senha."""
from apps.notifications.models import Notificacao, PedidoResetSenha


def notificar(utilizador, mensagem: str, link: str = "") -> Notificacao:
    """Cria uma notificação in-app (equivalente ao helper do Flask)."""
    return Notificacao.objects.create(
        utilizador=utilizador, mensagem=mensagem[:255], link=link[:255]
    )


def pedir_reset_senha(identificador: str) -> bool:
    """Regista um pedido de reset por telemóvel ou email.

    Devolve True se o pedido foi criado para uma conta existente.
    O envio real (SMS/email) deve ser enfileirado via Celery.
    """
    from apps.accounts.models import Usuario

    filtros = {"telemovel__iexact": identificador}
    if "@" in identificador:
        filtros = {"email__iexact": identificador}

    user = Usuario.objects.filter(**filtros).first()
    if user is None:
        return False

    PedidoResetSenha.objects.create(utilizador=user)
    # TODO: enfileirar envio SMS/email (substitui flask_mail/celery tasks antigos)
    return True
