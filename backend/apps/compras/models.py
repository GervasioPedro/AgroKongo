"""Motor transacional do AgroKongo: escrow, estados e auditoria.

Diferença crítica face ao sistema Flask anterior: `mudar_status()` agora
PERSISTE o registo de histórico na base de dados (no Flask o objeto era
criado e retornado mas nunca adicionado à sessão — tabela sempre vazia).
"""
import secrets
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel

TAXA_COMISSAO = Decimal("0.05")  # 5% para a plataforma, 95% para o vendedor


class Transacao(TimeStampedModel):
    class Statuses(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        AGUARDANDO_PAGAMENTO = "pendente_pagamento", "Aguardando pagamento"
        ANALISE = "pagamento_sob_analise", "Pagamento sob análise"
        ESCROW = "pago_escrow", "Pago em custódia (escrow)"
        ENVIADO = "mercadoria_enviada", "Mercadoria enviada"
        ENTREGUE = "mercadoria_entregue", "Mercadoria entregue"
        FINALIZADO = "finalizada", "Finalizada (liquidada)"
        CANCELADO = "cancelada", "Cancelada"
        DISPUTA = "em_disputa", "Em disputa"

    # Transições válidas do fluxo principal de custódia
    TRANSICOES_VALIDAS = {
        Statuses.PENDENTE: {Statuses.AGUARDANDO_PAGAMENTO, Statuses.CANCELADO},
        Statuses.AGUARDANDO_PAGAMENTO: {Statuses.ANALISE, Statuses.CANCELADO},
        Statuses.ANALISE: {Statuses.ESCROW, Statuses.CANCELADO},
        Statuses.ESCROW: {Statuses.ENVIADO, Statuses.DISPUTA, Statuses.CANCELADO},
        Statuses.ENVIADO: {Statuses.ENTREGUE, Statuses.DISPUTA},
        Statuses.ENTREGUE: {Statuses.FINALIZADO, Statuses.DISPUTA},
        Statuses.DISPUTA: {Statuses.FINALIZADO, Statuses.CANCELADO},
        Statuses.FINALIZADO: set(),
        Statuses.CANCELADO: set(),
    }

    fatura_ref = models.CharField(max_length=50, unique=True, db_index=True)

    safra = models.ForeignKey(
        "catalogo.Safra", on_delete=models.PROTECT, related_name="transacoes",
        db_column="safra_id",
    )
    comprador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="compras", db_column="comprador_id",
    )
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="vendas", db_column="vendedor_id",
    )

    quantidade_comprada = models.DecimalField(max_digits=12, decimal_places=2)
    valor_total_pago = models.DecimalField(max_digits=14, decimal_places=2)
    comissao_plataforma = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    valor_liquido_vendedor = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )

    status = models.CharField(
        max_length=30, choices=Statuses.choices, default=Statuses.PENDENTE,
        db_index=True,
    )
    data_pagamento_escrow = models.DateTimeField(null=True, blank=True)
    data_envio = models.DateTimeField(null=True, blank=True)
    data_entrega = models.DateTimeField(null=True, blank=True)
    data_liquidacao = models.DateTimeField(null=True, blank=True)
    previsao_entrega = models.DateTimeField(null=True, blank=True)

    comprovativo_path = models.CharField(max_length=255, blank=True)
    transferencia_concluida = models.BooleanField(default=False)

    class Meta:
        db_table = "transacoes"
        verbose_name = "Transação"
        verbose_name_plural = "Transações"
        ordering = ["-criado_em"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(comprador=models.F("vendedor")),
                name="ck_no_self_deal",
            ),
            models.CheckConstraint(
                condition=models.Q(valor_total_pago__gt=Decimal("0")),
                name="ck_total_pos",
            ),
        ]

    def __str__(self):
        return self.fatura_ref

    # --- Regras de negócio ---
    @staticmethod
    def gerar_fatura_ref() -> str:
        agora = timezone.localtime() if settings.USE_TZ else timezone.now()
        return f"AK-{agora:%Y%m%d}-{secrets.token_hex(3).upper()}"

    def calcular_split(self):
        """Divisão 95/5 do valor pago, arredondada em meia-alto."""
        total = Decimal(self.valor_total_pago)
        comissao = (total * TAXA_COMISSAO).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        liquido = (total - comissao).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.comissao_plataforma = comissao
        self.valor_liquido_vendedor = liquido

    def pode_transicionar(self, novo_status: str) -> bool:
        return novo_status in self.TRANSICOES_VALIDAS.get(self.status, set())

    def mudar_status(self, novo_status: str, observacao: str = ""):
        """Transiciona o estado e PERSISTE o registo no histórico.

        Lança ValueError se a transição não for válida — o call-site deve
        estar dentro de uma transação atómica.
        """
        if novo_status == self.status:
            return None
        if not self.pode_transicionar(novo_status):
            raise ValueError(
                f"Transição de estado inválida: {self.status} -> {novo_status}"
            )

        historico = HistoricoStatus.objects.create(
            transacao=self,
            status_anterior=self.status,
            status_novo=novo_status,
            observacao=observacao[:255],
        )
        self.status = novo_status

        stamps = {
            self.Statuses.ESCROW: "data_pagamento_escrow",
            self.Statuses.ENVIADO: "data_envio",
            self.Statuses.ENTREGUE: "data_entrega",
            self.Statuses.FINALIZADO: "data_liquidacao",
        }
        campo = stamps.get(novo_status)
        if campo:
            setattr(self, campo, timezone.now())

        self.save(update_fields=["status", campo, "atualizado_em"] if campo
                  else ["status", "atualizado_em"])
        return historico


class HistoricoStatus(models.Model):
    transacao = models.ForeignKey(
        Transacao, on_delete=models.CASCADE, related_name="historico",
        db_column="transacao_id",
    )
    status_anterior = models.CharField(max_length=30, blank=True)
    status_novo = models.CharField(max_length=30)
    data_mudanca = models.DateTimeField(default=timezone.now, db_index=True)
    observacao = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "historico_status"
        verbose_name = "Histórico de estado"
        verbose_name_plural = "Históricos de estado"
        ordering = ["data_mudanca"]

    def __str__(self):
        return f"{self.transacao_id}: {self.status_anterior} → {self.status_novo}"


class Comprovativo(models.Model):
    """Talão de transferência bancária enviado pelo comprador."""

    transacao = models.ForeignKey(
        Transacao, on_delete=models.CASCADE, related_name="comprovativos",
        db_column="transacao_id",
    )
    caminho = models.CharField(max_length=255)
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="comprovativos_enviados",
    )
    validado = models.BooleanField(default=False, db_index=True)
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="comprovativos_validados",
    )
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "comprovativos"
        verbose_name = "Comprovativo"
        verbose_name_plural = "Comprovativos"
        ordering = ["-enviado_em"]

    def __str__(self):
        return f"Comprovativo {self.pk} ({self.transacao_id})"
