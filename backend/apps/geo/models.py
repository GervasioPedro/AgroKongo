"""Divisão administrativa de Angola: Províncias e Municípios."""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Provincia(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    nome = models.CharField(max_length=50, unique=True)
    codigo = models.PositiveSmallIntegerField(
        unique=True, validators=[MinValueValidator(1), MaxValueValidator(25)]
    )
    area_km2 = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Dados populacionais (Censo 2024 — estimativas provisórias; fonte INE-Angola)
    populacao_2024 = models.BigIntegerField(null=True, blank=True)
    dados_populacionais_ano = models.PositiveSmallIntegerField(null=True, blank=True)
    fonte_dados_populacionais = models.CharField(max_length=120, blank=True)

    class Meta:
        db_table = "geo_provincias"
        verbose_name = "Província"
        verbose_name_plural = "Províncias"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Municipio(models.Model):
    nome = models.CharField(max_length=50)
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.CASCADE,
        related_name="municipios",
        db_column="provincia_id",
    )

    class Meta:
        db_table = "geo_municipios"
        verbose_name = "Município"
        verbose_name_plural = "Municípios"
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["nome", "provincia"], name="uq_municipio_por_provincia"
            )
        ]

    def __str__(self):
        return f"{self.nome} ({self.provincia.nome})"
