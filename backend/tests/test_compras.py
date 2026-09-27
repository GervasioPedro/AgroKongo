"""Testes do fluxo de compra com escrow — cobre o bug crítico do Flask:
o histórico de status deve ser PERSISTIDO a cada transição."""
from decimal import Decimal

import pytest

pytestmark = pytest.mark.django_db


@pytest.fixture
def transacao_reservada(client, comprador, safra_disponivel):
    from conftest import autenticar

    autenticar(client, comprador)
    resp = client.post("/api/v1/transacoes/reservar", {
        "safra": safra_disponivel.id, "quantidade": 10,
    }, format="json")
    assert resp.status_code == 201, resp.data
    return resp.data


class TestReserva:
    def test_reserva_calcula_split_correto(self, transacao_reservada):
        # 10 kg x 250 = 2500; comissão 5% = 125; líquido vendedor = 2375
        assert Decimal(transacao_reservada["valor_total_pago"]) == Decimal("2500.0")
        assert Decimal(transacao_reservada["comissao_plataforma"]) == Decimal("125.0")
        assert Decimal(transacao_reservada["valor_liquido_vendedor"]) == Decimal("2375.0")
        assert transacao_reservada["status"] == "pendente_pagamento"

    def test_reserva_baixa_estoque(self, client, comprador, safra_disponivel):
        from conftest import autenticar

        autenticar(client, comprador)
        client.post("/api/v1/transacoes/reservar", {
            "safra": safra_disponivel.id, "quantidade": 10,
        }, format="json")
        safra_disponivel.refresh_from_db()
        assert safra_disponivel.quantidade_disponivel == Decimal("90.0")

    def test_reserva_sem_kyc_e_bloqueada(self, client, dados_geo):
        from apps.accounts.models import Usuario

        u = Usuario.objects.create_user(
            nome="Sem KYC", telemovel="+244933777888", senha="12345678",
            tipo=Usuario.Tipos.COMPRADOR, provincia=dados_geo[0],
        )
        from conftest import autenticar

        autenticar(client, u)
        resp = client.post("/api/v1/transacoes/reservar", {
            "safra": 1, "quantidade": 5,
        }, format="json")
        assert resp.status_code in (401, 403)

    def test_reserva_quantidade_maior_que_estoque(self, client, comprador, safra_disponivel):
        from conftest import autenticar

        autenticar(client, comprador)
        resp = client.post("/api/v1/transacoes/reservar", {
            "safra": safra_disponivel.id, "quantidade": 500,
        }, format="json")
        assert resp.status_code == 400

    def test_comprador_nao_pode_comprar_a_propria_safra(self, produtor, safra_disponivel, client):
        from conftest import autenticar

        autenticar(client, produtor)
        resp = client.post("/api/v1/transacoes/reservar", {
            "safra": safra_disponivel.id, "quantidade": 1,
        }, format="json")
        assert resp.status_code == 400


class TestHistoricoPersistido:
    """REGRESSÃO: no Flask, mudar_status() criava HistoricoStatus sem salvar."""

    def test_historico_tem_registros_apos_fluxo(self, client, admin, comprador,
                                                 produtor, transacao_reservada):
        tid = transacao_reservada["id"]
        # Admin confirma pagamento → escrow
        resp = client.post("/api/v1/auth", {
            "acao": "login", "telemovel": admin.telemovel, "senha": "AgroAdmin2026",
        }, format="json")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['token']}")
        r = client.post(f"/api/v1/transacoes/{tid}/confirmar-pagamento", {}, format="json")
        assert r.status_code == 200, r.data

        # Produtor envia mercadoria
        from conftest import autenticar

        autenticar(client, produtor)
        r = client.post(f"/api/v1/transacoes/{tid}/enviar", {}, format="json")
        assert r.status_code == 200, r.data

        # Comprador confirma entrega
        autenticar(client, comprador)
        r = client.post(f"/api/v1/transacoes/{tid}/confirmar-entrega", {}, format="json")
        assert r.status_code == 200, r.data

        # Histórico via API
        r = client.get(f"/api/v1/transacoes/{tid}/historico")
        assert r.status_code == 200
        estados = [h["status_novo"] for h in r.data]
        assert len(r.data) >= 3, f"Histórico vazio/incompleto: {r.data}"
        assert "pago_escrow" in estados
        assert "mercadoria_enviada" in estados
        assert "mercadoria_entregue" in estados

    def test_transicao_invalida_e_rejeitada(self, client, comprador, transacao_reservada):
        """Comprador tenta enviar mercadoria (ação do vendedor) → 403/409."""
        from conftest import autenticar

        autenticar(client, comprador)
        tid = transacao_reservada["id"]
        resp = client.post(f"/api/v1/transacoes/{tid}/enviar", {}, format="json")
        assert resp.status_code in (403, 409)


class TestLiquidacaoEscrow:
    def test_liquidacao_liberta_fundos_e_finaliza(self, client, admin, comprador,
                                                  transacao_reservada):
        from apps.compras.models import Transacao

        tid = transacao_reservada["id"]
        # leva até entregue
        resp = client.post("/api/v1/auth", {
            "acao": "login", "telemovel": admin.telemovel, "senha": "AgroAdmin2026",
        }, format="json")
        token_admin = resp.data["token"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_admin}")
        assert client.post(f"/api/v1/transacoes/{tid}/confirmar-pagamento", {},
                           format="json").status_code == 200

        from conftest import autenticar

        autenticar(client, comprador)
        vendedor = Transacao.objects.get(pk=tid).vendedor
        autenticar(client, vendedor)
        assert client.post(f"/api/v1/transacoes/{tid}/enviar", {},
                           format="json").status_code == 200
        autenticar(client, comprador)
        assert client.post(f"/api/v1/transacoes/{tid}/confirmar-entrega", {},
                           format="json").status_code == 200

        # Admin liquida
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_admin}")
        resp = client.post(f"/api/v1/transacoes/{tid}/liquidar", {}, format="json")
        assert resp.status_code == 200, resp.data
        assert resp.data["status"] == "finalizada"

        t = Transacao.objects.get(pk=tid)
        assert t.valor_liquido_vendedor == Decimal("2375.0")
        vendas = type(vendedor).objects.get(pk=vendedor.pk).vendas_concluidas
        assert vendas == 1
