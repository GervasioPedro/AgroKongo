"""Fixtures compartilhadas da suíte de testes AgroKongo (Django).

Correção face ao Flask: nenhuma dependência externa (Redis) — os settings
de teste usam LocMemCache e SQLite em memória, e a autenticação é feita por
token de sessão próprio criado no banco de teste.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

Usuario = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def dados_geo(db):
    """Província + município para as fixtures de utilizadores.

    Provincia usa PK numérica explícita (código oficial angolano), por isso
    o id é informado no create — igual ao comando `seed`.
    """
    from apps.geo.models import Municipio, Provincia

    prov = Provincia.objects.create(id=1, nome="Bengo", codigo=1)
    mun = Municipio.objects.create(nome="Dande", provincia=prov)
    return prov, mun


@pytest.fixture
def admin(dados_geo):
    prov, _ = dados_geo
    return Usuario.objects.create_user(
        nome="Admin AgroKongo", telemovel="+244920000000",
        senha="AgroAdmin2026", tipo=Usuario.Tipos.ADMIN, provincia=prov,
    )


@pytest.fixture
def produtor(dados_geo):
    prov, mun = dados_geo
    u = Usuario.objects.create_user(
        nome="Manuel Produtor", telemovel="+244923000000",
        senha="12345678", tipo=Usuario.Tipos.PRODUTOR, provincia=prov,
        municipio=mun, email="produtor@agrokongo.ao",
    )
    u.conta_validada = True  # KYC aprovado
    u.documento_pdf = "kyc_produtor.pdf"
    u.nif = "5400123456"
    u.iban = "AO06000000000000000000001"
    u.perfil_completo = True
    u.save()
    return u


@pytest.fixture
def comprador(dados_geo):
    prov, mun = dados_geo
    u = Usuario.objects.create_user(
        nome="Ana Compradora", telemovel="+244931000000",
        senha="12345678", tipo=Usuario.Tipos.COMPRADOR, provincia=prov,
        municipio=mun, email="compradora@agrokongo.ao",
    )
    u.conta_validada = True
    u.documento_pdf = "kyc_compradora.pdf"
    u.perfil_completo = True
    u.save()
    return u


@pytest.fixture
def produto(dados_geo):
    from apps.catalogo.models import Produto

    return Produto.objects.create(
        nome="Batata Reunta", categoria="Tubérculos",
    )


@pytest.fixture
def safra_disponivel(produto, produtor):
    from decimal import Decimal

    from apps.catalogo.models import Safra

    return Safra.objects.create(
        produtor=produtor, produto=produto,
        quantidade_disponivel=Decimal("100.0"), unidade="kg",
        preco_por_unidade=Decimal("250.0"),
    )


def autenticar(client, usuario):
    """Login via endpoint real → devolve o token Bearer e autoriza o client."""
    resp = client.post(
        "/api/v1/auth",
        {"acao": "login", "telemovel": usuario.telemovel, "senha": "12345678"},
        format="json",
    )
    assert resp.status_code == 200, resp.data
    token = resp.data["token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return token
