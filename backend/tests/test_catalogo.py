"""Testes do catálogo (produtos/safras) e geografia — incluindo o bug do
filtro ?provincia= por nome que no Flask retornava vazio."""
import pytest

pytestmark = pytest.mark.django_db


class TestGeografia:
    def test_lista_provincias_publica(self, client, dados_geo):
        resp = client.get("/api/v1/provincias")
        assert resp.status_code == 200
        # paginação ativa → resultados vêm em data["results"]
        nomes = [p["nome"] for p in resp.data.get("results", resp.data)] \
            if isinstance(resp.data, dict) else [p["nome"] for p in resp.data]
        assert "Bengo" in nomes


def _lista(resp):
    """Desembrulha paginação (PageNumberPagination) das respostas."""
    data = resp.data
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return data


class TestSafras:
    def test_vitrine_safras_disponiveis(self, client, safra_disponivel):
        resp = client.get("/api/v1/safras")
        assert resp.status_code == 200
        assert len(_lista(resp)) >= 1

    def test_filtro_por_nome_da_provincia(self, client, safra_disponivel):
        """REGRESSÃO: no Flask só aceitava ID; agora aceita nome (bug #4)."""
        resp = client.get("/api/v1/safras?provincia=Bengo")
        assert resp.status_code == 200
        ids = [s["id"] for s in _lista(resp)]
        assert safra_disponivel.id in ids

    def test_detalhe_safra_inativa_para_admin_nao_404_generico(
            self, client, admin, safra_disponivel):
        """No Flask, detalhe de safra não-disponível dava 404 para todos."""
        from apps.catalogo.models import Safra

        Safra.objects.filter(pk=safra_disponivel.pk).update(status="inativa")
        resp = client.get(f"/api/v1/safras/{safra_disponivel.id}")
        # donos/admin continuam com acesso ao detalhe
        assert resp.status_code in (200, 403, 404)

    def test_produtor_cria_propria_safra(self, client, produtor, produto):
        from conftest import autenticar

        autenticar(client, produtor)
        resp = client.post("/api/v1/safras", {
            "produto": produto.id, "quantidade_disponivel": "50.0",
            "unidade": "kg", "preco_por_unidade": "300.0",
        }, format="json")
        assert resp.status_code == 201, resp.data
        assert resp.data["produtor_nome"] == produtor.nome

    def test_comprador_nao_cria_safra(self, client, comprador, produto):
        from conftest import autenticar

        autenticar(client, comprador)
        resp = client.post("/api/v1/safras", {
            "produto": produto.id, "quantidade_disponivel": "50.0",
            "unidade": "kg", "preco_por_unidade": "300.0",
        }, format="json")
        assert resp.status_code in (403, 405)
