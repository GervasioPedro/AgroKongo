"""
Testes Unitários dos Serviços
Testa a lógica de negócio isoladamente das rotas HTTP.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone

from app.extensions import db
from app.models import Usuario, Provincia, Municipio, Notificacao, LogAuditoria
from app.services.usuario_service import UsuarioService
from app.services.pagamento_service import PagamentoService


class TestUsuarioService:
    """Testes para o serviço de gestão de usuários."""
    
    @pytest.fixture
    def setup_admin(self, app, db):
        """Cria um admin de teste e retorna o ID."""
        # Nao usar with app.app_context() para manter sessao ativa
        admin = Usuario(
            nome="Admin Teste",
            telemovel="900000001",
            email="admin@teste.com",
            tipo="admin",
            perfil_completo=True,
            conta_validada=True
        )
        admin.senha = "admin123"
        db.session.add(admin)
        db.session.commit()
        return int(admin.id)  # Retorna ID como int
    
    @pytest.fixture
    def setup_usuario_pendente(self, app, db):
        """Cria um usuario pendente de validacao e retorna o ID."""
        # Nao usar with app.app_context() para manter sessao ativa
        # Criar localizacao
        prov = Provincia(nome='Luanda')
        db.session.add(prov)
        db.session.flush()
        
        mun = Municipio(nome='Belas', provincia_id=prov.id)
        db.session.add(mun)
        db.session.flush()
        
        usuario = Usuario(
            nome="Jose Teste",
            telemovel="923000002",
            email="jose@teste.com",
            tipo="produtor",
            nif="501234400002",
            iban="AO06004000001234567890124",
            municipio_id=mun.id,
            provincia_id=prov.id,
            perfil_completo=True,
            conta_validada=False  # Pendente
        )
        usuario.senha = "123456"
        db.session.add(usuario)
        db.session.commit()
        return int(usuario.id)  # Retorna ID como int
    
    def test_validar_usuario_sucesso(self, app, db, setup_admin, setup_usuario_pendente):
        """Testa validacao bem-sucedida de usuario."""
        with app.app_context():
            admin_id = setup_admin  # Agora e ID
            usuario_id = setup_usuario_pendente  # Agora e ID
            
            # Buscar objetos no session atual
            admin = Usuario.query.get(admin_id)
            usuario = Usuario.query.get(usuario_id)
            
            assert usuario is not None
            assert usuario.conta_validada is False
            
            sucesso, msg = UsuarioService.validar_usuario(
                user_id=usuario.id,
                admin_id=admin.id
            )
            
            assert sucesso is True
            assert "validado com sucesso" in msg.lower()
            
            # Verificar se usuario foi atualizado
            usuario_atualizado = Usuario.query.get(usuario.id)
            assert usuario_atualizado.conta_validada is True
            
            # Verificar notificacao criada
            notificacao = Notificacao.query.filter_by(usuario_id=usuario.id).first()
            assert notificacao is not None
            assert "validada" in notificacao.mensagem.lower()
    
    def test_rejeitar_usuario_com_motivo(self, app, db, setup_admin, setup_usuario_pendente):
        """Testa rejeicao de usuario com motivo."""
        with app.app_context():
            admin_id = setup_admin  # Agora e ID
            usuario_id = setup_usuario_pendente  # Agora e ID
            
            # Buscar objetos no session atual
            admin = Usuario.query.get(admin_id)
            usuario = Usuario.query.get(usuario_id)
            
            motivo = "Documentacao incompleta"
            
            sucesso, msg = UsuarioService.rejeitar_usuario(
                user_id=usuario.id,
                admin_id=admin.id,
                motivo=motivo
            )
            
            assert sucesso is True
            
            # Verificar usuario rejeitado
            usuario_atualizado = Usuario.query.get(usuario.id)
            assert usuario_atualizado.conta_validada is False
            assert usuario_atualizado.perfil_completo is False
            
            # Verificar notificacao com motivo
            notificacao = Notificacao.query.filter_by(usuario_id=usuario.id).first()
            assert notificacao is not None
            assert motivo in notificacao.mensagem
    
    def test_verificar_perfil_completo(self, app, db):
        """Testa verificação de completude do perfil."""
        with app.app_context():
            # Criar usuário incompleto
            usuario_incompleto = Usuario(
                nome="Teste Incompleto",
                telemovel="931000003",
                email="incompleto@teste.com",
                tipo="comprador"
                # Sem NIF, sem localização
            )
            usuario_incompleto.senha = "123456"
            db.session.add(usuario_incompleto)
            db.session.commit()
            
            # Perfil deve estar incompleto
            assert UsuarioService.verificar_perfil_completo(usuario_incompleto) is False


class TestPagamentoService:
    """Testes para o serviço de gestão de pagamentos."""
    
    def test_calcular_comissao_valores_exatos(self):
        """Testa cálculo preciso de comissão."""
        # Teste com valor redondo
        comissao, liquido = PagamentoService.calcular_comissao(Decimal('10000.00'))
        assert comissao == Decimal('500.00')
        assert liquido == Decimal('9500.00')
        
        # Teste com valor quebrado
        comissao, liquido = PagamentoService.calcular_comissao(Decimal('1234.56'))
        assert comissao == Decimal('61.73')
        assert liquido == Decimal('1172.83')
        
        # Teste com valor pequeno
        comissao, liquido = PagamentoService.calcular_comissao(Decimal('10.00'))
        assert comissao == Decimal('0.50')
        assert liquido == Decimal('9.50')
    
    def test_calcular_comissao_taxa_personalizada(self):
        """Testa cálculo com taxa diferente da padrão."""
        valor = Decimal('10000.00')
        taxa = Decimal('0.10')  # 10%
        
        comissao, liquido = PagamentoService.calcular_comissao(valor, taxa)
        assert comissao == Decimal('1000.00')
        assert liquido == Decimal('9000.00')
    
    def test_precisao_decimal(self):
        """Garante que não há erros de ponto flutuante."""
        # Este é um teste crítico para marketplace financeiro
        valores_teste = [
            Decimal('999.99'),
            Decimal('1000.01'),
            Decimal('0.01'),
            Decimal('99999.99')
        ]
        
        for valor in valores_teste:
            comissao, liquido = PagamentoService.calcular_comissao(valor)
            # A soma deve ser exatamente igual ao original
            assert (comissao + liquido) == valor
