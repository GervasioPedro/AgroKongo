"""Utilizadores do AgroKongo (produtor, comprador, admin).

Substitui o modelo Flask-SQLAlchemy/Flask-Login por um User customizado do
Django. A autenticação na API é feita com JWT próprio (apps.accounts.auth),
sem dependências externas.
"""
import re
from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel

TELEFONE_ANGOLA_REGEX = r"^(\+244|244)?[9][1-9][0-9]{7}$"


def validar_telemovel(valor: str) -> str:
    """Normaliza para +244 e valida o formato de número angolano."""
    digitos = re.sub(r"\D", "", valor or "")
    if digitos.startswith("244"):
        digitos = digitos[3:]
    if not re.fullmatch(r"[9][1-9][0-9]{7}", digitos):
        raise ValueError(
            "Número de telefone inválido. Use o formato 9XX XXX XXX."
        )
    return f"+244{digitos}"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, telemovel, nome, senha, **extra):
        if not nome:
            raise ValueError("O nome é obrigatório.")
        telemovel = validar_telemovel(telemovel)
        email = extra.pop("email", "") or None
        user = self.model(telemovel=telemovel, nome=nome, email=email, **extra)
        user.set_password(senha)
        user.save(using=self._db)
        return user

    def create_user(self, telemovel, nome, senha=None, **extra):
        extra.setdefault("tipo", Usuario.Tipos.COMPRADOR)
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(telemovel, nome, senha, **extra)

    def create_superuser(self, telemovel, nome="Admin", senha=None, **extra):
        extra.setdefault("tipo", Usuario.Tipos.ADMIN)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("conta_validada", True)
        return self._create_user(telemovel, nome, senha, **extra)


class Usuario(TimeStampedModel, AbstractBaseUser, PermissionsMixin):
    class Tipos(models.TextChoices):
        ADMIN = "admin", "Administrador"
        PRODUTOR = "produtor", "Produtor"
        COMPRADOR = "comprador", "Comprador"

    nome = models.CharField(max_length=100)
    telemovel = models.CharField(
        max_length=20,
        unique=True,
        error_messages={"unique": "Já existe uma conta com este número de telemóvel."},
    )
    email = models.EmailField(
        max_length=120,
        unique=True,
        null=True,
        blank=True,
        error_messages={"unique": "Já existe uma conta com este email."},
    )
    tipo = models.CharField(max_length=20, choices=Tipos.choices, db_index=True)

    nif = models.CharField(max_length=20, unique=True, null=True, blank=True)
    iban = models.CharField(max_length=34, blank=True)

    rating_vendedor = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal("5.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    vendas_concluidas = models.PositiveIntegerField(default=0)

    foto_perfil = models.CharField(max_length=150, default="default_user.jpg")
    documento_pdf = models.CharField(max_length=150, blank=True)
    perfil_completo = models.BooleanField(default=False)
    conta_validada = models.BooleanField(default=False, db_index=True)

    provincia = models.ForeignKey(
        "geo.Provincia", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="utilizadores",
    )
    municipio = models.ForeignKey(
        "geo.Municipio", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="utilizadores",
    )

    saldo_disponivel = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )

    # Campos Django (login no admin / permissões)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    data_ultimo_acesso = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "telemovel"
    REQUIRED_FIELDS = ["nome"]

    class Meta:
        db_table = "usuarios"
        verbose_name = "Utilizador"
        verbose_name_plural = "Utilizadores"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.nome} ({self.telemovel})"

    def save(self, *args, **kwargs):
        self.telemovel = validar_telemovel(self.telemovel)
        super().save(*args, **kwargs)

    # --- Helpers de negócio ---
    @property
    def eh_produtor(self):
        return self.tipo == self.Tipos.PRODUTOR

    @property
    def eh_comprador(self):
        return self.tipo == self.Tipos.COMPRADOR

    @property
    def eh_admin(self):
        return self.tipo == self.Tipos.ADMIN or self.is_superuser

    @property
    def kyc_aprovado(self):
        return self.conta_validada and bool(self.documento_pdf)

    def get_full_name(self):
        return self.nome

    def get_short_name(self):
        return self.nome.split(" ")[0] if self.nome else ""


class SessaoAPI(models.Model):
    """Sessão de API baseada em token opaco (equivalente à sessão Flask).

    Cada request autenticado renova `ultima_atividade`, permitindo expiração
    por inatividade como no sistema antigo.
    """

    utilizador = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="sessoes"
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    ultima_atividade = models.DateTimeField(auto_now=True)
    ativa = models.BooleanField(default=True)
    user_agent = models.CharField(max_length=200, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "sessions_api"
        verbose_name = "Sessão de API"
        verbose_name_plural = "Sessões de API"

    def __str__(self):
        return f"Sessão {self.utilizador_id} @ {self.criado_em:%d/%m/%Y %H:%M}"
