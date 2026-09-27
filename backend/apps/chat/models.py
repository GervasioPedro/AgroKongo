"""Chat entre comprador e vendedor de uma transação."""
from django.conf import settings
from django.db import models


class Mensagem(models.Model):
    transacao = models.ForeignKey(
        "compras.Transacao", on_delete=models.CASCADE, related_name="mensagens",
        db_column="transacao_id", null=True, blank=True,
    )
    remetente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="mensagens_enviadas", db_column="remetente_id",
    )
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="mensagens_recebidas", db_column="destinatario_id",
    )
    conteudo = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True, db_index=True)
    lida = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "mensagens"
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ["data_envio"]

    def __str__(self):
        return f"{self.remetente_id} → {self.destinatario_id}: {self.conteudo[:30]}"
