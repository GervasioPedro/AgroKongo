"""Modelos base partilhados por todas as apps do AgroKongo."""
from django.db import models


class TimeStampedModel(models.Model):
    """Adiciona datas de criação/atualização automáticas (UTC)."""

    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
