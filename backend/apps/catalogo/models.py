"""Catálogo: produtos e safra (anúncio de venda do produtor)."""
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class Produto(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    categoria = models.CharField(max_length=50, db_index=True, blank=True)

    class Meta:
        db_table = "produtos"
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Safra(TimeStampedModel):
    class Statuses(models.TextChoices):
        DISPONIVEL = "disponivel", "Disponível"
        ESGOTADA = "esgotada", "Esgotada"
        INATIVA = "inativa", "Inativa"

    produtor = models.ForeignKey(
        "accounts.Usuario", on_delete=models.CASCADE, related_name="safras",
        db_column="produtor_id",
    )
    produto = models.ForeignKey(
        Produto, on_delete=models.PROTECT, related_name="safras",
        db_column="produto_id",
    )
    quantidade_disponivel = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    unidade = models.CharField(max_length=20, default="kg")
    preco_por_unidade = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    status = models.CharField(
        max_length=20, choices=Statuses.choices, default=Statuses.DISPONIVEL,
        db_index=True,
    )
    imagem = models.CharField(max_length=150, default="default_safra.webp")
    observacoes = models.TextField(blank=True)

    class Meta:
        db_table = "safras"
        verbose_name = "Safra"
        verbose_name_plural = "Safras"
        ordering = ["-criado_em"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantidade_disponivel__gte=Decimal("0")),
                name="ck_stock_pos",
            ),
            models.CheckConstraint(
                condition=models.Q(preco_por_unidade__gt=Decimal("0")),
                name="ck_preco_pos",
            ),
        ]
        indexes = [
            # Otimiza a vitrine do mercado
            models.Index(fields=["produto", "status"], name="idx_safra_prod_status"),
        ]

    def __str__(self):
        return f"Safra {self.pk} - {self.status}"

    @property
    def valor_estimado(self) -> Decimal:
        return (self.quantidade_disponivel * self.preco_por_unidade).quantize(
            Decimal("0.01")
        )

    @property
    def imagem_url(self):
        if not self.imagem:
            return None
        return f"/uploads/safras/{self.imagem}"
