"""Testes de autenticação e utilizadores."""
import pytest

pytestmark = pytest.mark.django_db


class TestRegisto:
    def test_registo_sucesso(self, client):
        resp = client.post("/api/v1/auth", {
            "acao": "registo", "nome": "Joao Teste",
            "telemovel": "+244933000111", "senha": "segredo123",
            "confirmar_senha": "segredo123", "tipo": "comprador",
        }, format="json")
        assert resp.status_code == 201, resp.data
        assert resp.data["utilizador"]["telemovel"] == "+244933000111"

    def test_registo_telemovel_invalido(self, client):
        resp = client.post("/api/v1/auth", {
            "acao": "registo", "nome": "Joao", "telemovel": "12345",
            "senha": "segredo123", "confirmar_senha": "segredo123",
        }, format="json")
        assert resp.status_code == 400

    def test_registo_senhas_diferentes(self, client):
        resp = client.post("/api/v1/auth", {
            "acao": "registo", "nome": "Joao", "telemovel": "+244933000222",
            "senha": "segredo123", "confirmar_senha": "outraSenha1",
        }, format="json")
        assert resp.status_code == 400
        # handler central normaliza para {erro, campos}
        assert "confirmar_senha" in str(resp.data)


class TestLoginLogout:
    def test_login_credenciais_validas(self, client, comprador):
        from conftest import autenticar

        token = autenticar(client, comprador)
        assert token
        # valida o token numa rota protegida real
        resp = client.get("/api/v1/transacoes")
        assert resp.status_code == 200

    def test_login_credenciais_invalidas(self, client, comprador):
        resp = client.post("/api/v1/auth", {
            "acao": "login", "telemovel": comprador.telemovel,
            "senha": "senha-errada-999",
        }, format="json")
        assert resp.status_code == 401

    def test_rota_protegida_sem_token(self, client):
        resp = client.get("/api/v1/transacoes")
        assert resp.status_code in (401, 403)

    def test_logout_invalida_token(self, client, comprador):
        from conftest import autenticar

        autenticar(client, comprador)
        resp = client.post("/api/v1/auth", {"acao": "logout"}, format="json")
        assert resp.status_code == 200
        # token morto → não autentica mais
        resp = client.get("/api/v1/transacoes")
        assert resp.status_code in (401, 403)


class TestRBAC:
    def test_nao_admin_nao_lista_utilizadores(self, client, comprador):
        from conftest import autenticar

        autenticar(client, comprador)
        resp = client.get("/api/v1/utilizadores")
        assert resp.status_code == 403

    def test_admin_lista_utilizadores(self, client, admin):
        from conftest import autenticar

        resp = client.post("/api/v1/auth", {
            "acao": "login", "telemovel": admin.telemovel,
            "senha": "AgroAdmin2026",
        }, format="json")
        assert resp.status_code == 200, resp.data
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['token']}")
        resp = client.get("/api/v1/utilizadores")
        assert resp.status_code == 200


class TestAtualizarPerfil:
    """PATCH /utilizadores/me — endpoint novo usado pelo React."""

    def test_atualizar_me_preenche_nif_iban(self, client, comprador):
        from conftest import autenticar
        autenticar(client, comprador)
        resp = client.patch("/api/v1/utilizadores/me", {
            "nif": "5400999999", "iban": "AO06000000000000000000009",
        }, format="json")
        assert resp.status_code == 200
        assert resp.data["nif"] == "5400999999"

    def test_me_bloqueia_elevacao_de_privilgios(self, client, comprador):
        from conftest import autenticar
        autenticar(client, comprador)
        client.patch("/api/v1/utilizadores/me", {
            "tipo": "admin", "conta_validada": True,
        }, format="json")
        comprador.refresh_from_db()
        assert comprador.tipo == "comprador"
        assert comprador.conta_validada is True  # já era true na fixture

    def test_me_exige_autenticacao(self, client):
        resp = client.patch("/api/v1/utilizadores/me", {"nome": "X"},
                            format="json")
        assert resp.status_code in (401, 403)
