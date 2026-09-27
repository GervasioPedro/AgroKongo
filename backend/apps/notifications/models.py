"""Notificações in-app e pedidos de recuperação de senha."""
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Notificacao(models.Model):
    utilizador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="notificacoes", db_column="usuario_id",
    )
    mensagem = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    lida = models.BooleanField(default=False, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "notificacoes"
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Notificação para {self.utilizador_id}: {self.mensagem[:40]}"


class PedidoResetSenha(models.Model):
    """Pedido de recuperação de senha com código numérico temporário."""

    utilizador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="pedidos_reset",
    )
    codigo = models.CharField(max_length=6, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "pedidos_reset_senha"
        verbose_name = "Pedido de reset de senha"
        verbose_name_plural = "Pedidos de reset de senha"
        ordering = ["-criado_em"]

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = f"{secrets.randbelow(1000000):06d}"
        super().save(*args, **kwargs)

    @property
    def expirado(self) -> bool:
        validade = timedelta(minutes=getattr(settings, "RESET_TOKEN_MINUTES", 30))
        return timezone.now() - self.criado_em > validade
