"""Autenticação própria por token (equivalente ao JWT de sessão do Flask).

Sem dependências externas: tokens opacos aleatórios guardados em `SessaoAPI`,
com expiração por inatividade. Em produção, trocar por djangorestframework-simplejwt
ou Auth de domínio se necessário.
"""
import secrets

from django.conf import settings
from django.utils import timezone
from rest_framework import authentication, exceptions


class TokenAuthentication(authentication.BaseAuthentication):
    """Espera o header `Authorization: Bearer <token>`."""

    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).split()
        if not header or header[0].lower() != self.keyword.lower().encode():
            return None
        try:
            token = header[1].decode()
        except UnicodeError:
            raise exceptions.AuthenticationFailed("Token inválido.")

        return self._authenticate_token(request, token)

    def _authenticate_token(self, request, token: str):
        from apps.accounts.models import SessaoAPI

        sessao = (
            SessaoAPI.objects.select_related("utilizador")
            .filter(token=token, ativa=True)
            .first()
        )
        if sessao is None:
            raise exceptions.AuthenticationFailed("Sessão inválida ou terminada.")

        limiar = timezone.now() - timezone.timedelta(
            minutes=settings.SESSION_INACTIVE_TIMEOUT_MINUTES
        )
        if sessao.ultima_atividade < limiar:
            sessao.ativa = False
            sessao.save(update_fields=["ativa"])
            raise exceptions.AuthenticationFailed("Sessão expirada por inatividade.")

        user = sessao.utilizador
        if not user.is_active:
            raise exceptions.AuthenticationFailed("Conta desativada.")

        # Renova atividade (slide expiration) sem carregar tudo de novo
        SessaoAPI.objects.filter(pk=sessao.pk).update(ultima_atividade=timezone.now())
        request.sessao_api = sessao
        return (user, sessao)

    def authenticate_header(self, request):
        return self.keyword


def criar_sessao(user, request=None) -> str:
    """Cria uma sessão de API e devolve o token em texto (mostrado 1 só vez)."""
    from apps.accounts.models import SessaoAPI

    token = secrets.token_hex(32)
    SessaoAPI.objects.create(
        utilizador=user,
        token=token,
        user_agent=(request.META.get("HTTP_USER_AGENT", "")[:200]
                    if request else ""),
        ip=_ip_da_request(request),
    )
    return token


def encerrar_sessao(request) -> bool:
    sessao = getattr(request, "sessao_api", None)
    if sessao is None:
        return False
    sessao.ativa = False
    sessao.save(update_fields=["ativa"])
    return True


def _ip_da_request(request):
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
