"""
Testes Unitários de Autenticação e Segurança
Cobertura: Login, Registro, Validação de Dados, CSRF
"""
import os
import sys
from pathlib import Path

# Adicionar root do projeto ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from app.models import Usuario, Provincia, Municipio
from app.extensions import db


class TestUsuarioValidacao:
    """Testes de validação do modelo Usuario"""
    
    def test_validar_telemovel_valido(self):
        """Testa validação de telemóvel angolano válido"""
        usuario = Usuario(
            nome='João Silva',
            email='joao@example.com',
            senha='senha123',
            tipo='comprador'
        )
        
        # Telemóvel válido (9 digits, starting with 9)
        usuario.telemovel = '923456789'
        assert usuario.telemovel == '923456789'
    
    def test_validar_telemovel_com_codigo_pais(self):
        """Testa remoção automática do código +244"""
        usuario = Usuario(
            nome='Maria Santos',
            email='maria@example.com',
            senha='senha123',
            tipo='produtor'
        )
        
        # Telemóvel com código +244
        usuario.telemovel = '+244923456789'
        assert usuario.telemovel == '923456789'
    
    def test_validar_telemovel_invalido(self):
        """Testa rejeição de telemóvel inválido"""
        usuario = Usuario(
            nome='Pedro Costa',
            email='pedro@example.com',
            senha='senha123',
            tipo='comprador'
        )
        
        # Telemóvel inválido (não começa com 9)
        with pytest.raises(ValueError, match="Formato AO inválido"):
            usuario.telemovel = '823456789'
    
    def test_validar_telemovel_vazio(self):
        """Testa rejeição de telemóvel vazio"""
        usuario = Usuario(
            nome='Ana Oliveira',
            email='ana@example.com',
            senha='senha123',
            tipo='comprador'
        )
        
        with pytest.raises(ValueError, match="Telemovel.*vazio"):
            usuario.telemovel = None
    
    def test_validar_email_conversao_lowercase(self):
        """Testa conversão automática de email para lowercase"""
        usuario = Usuario(
            nome='Carlos Ferreira',
            email='CARLOS@EXAMPLE.COM',
            senha='senha123',
            tipo='comprador'
        )
        
        assert usuario.email == 'carlos@example.com'
    
    def test_validar_email_invalido(self):
        """Testa rejeição de email sem @"""
        # Email inválido deve lançar ValueError durante a construção
        with pytest.raises(ValueError, match="Email.*válido"):
            Usuario(
                nome='Lucia Rodrigues',
                email='lucia.example.com',  # Sem @ - inválido
                senha='senha123',
                tipo='comprador'
            )
    
    def test_validar_nif_conversao_uppercase(self):
        """Testa conversão automática de NIF para uppercase"""
        usuario = Usuario(
            nome='Francisco Manuel',
            email='francisco@example.com',
            senha='senha123',
            tipo='produtor'
        )
        
        usuario.nif = 'abc123456'
        assert usuario.nif == 'ABC123456'
    
    def test_validar_nif_curto(self):
        """Testa rejeição de NIF com menos de 9 caracteres"""
        usuario = Usuario(
            nome='Teresa Almeida',
            email='teresa@example.com',
            senha='senha123',
            tipo='produtor'
        )
        
        with pytest.raises(ValueError, match="NIF.*válido"):
            usuario.nif = '12345678'
    
    def test_set_senha_minima(self):
        """Testa definição de senha com tamanho mínimo"""
        usuario = Usuario(
            nome='Ricardo Sousa',
            email='ricardo@example.com',
            senha='senha123',
            tipo='comprador'
        )
        
        # Senha mínima (6 caracteres)
        usuario.set_senha('123456')
        assert usuario.senha is not None
        assert usuario.senha_hash is not None
        assert usuario.senha != '123456'  # Deve estar hash
    
    def test_set_senha_curta(self):
        """Testa rejeição de senha muito curta"""
        usuario = Usuario(
            nome='Patricia Dias',
            email='patricia@example.com',
            senha='senha123',
            tipo='comprador'
        )
        
        with pytest.raises(ValueError, match="Senha deve ter pelo menos 6 caracteres"):
            usuario.set_senha('12345')
    
    def test_verificar_senha_correta(self):
        """Testa verificação de senha correta"""
        usuario = Usuario(
            nome='Bruno Fernandes',
            email='bruno@example.com',
            senha='senha123',
            tipo='comprador'
        )
        
        senha_teste = 'MinhaSenha123'
        usuario.set_senha(senha_teste)
        
        assert usuario.verificar_senha(senha_teste) is True
    
    def test_verificar_senha_incorreta(self):
        """Testa verificação de senha incorreta"""
        usuario = Usuario(
            nome='Catarina Lopes',
            email='catarina@example.com',
            senha='senha123',
            tipo='comprador'
        )
        
        usuario.set_senha('SenhaCorreta123')
        
        assert usuario.verificar_senha('SenhaErrada456') is False
    
    def test_verificar_senha_vazia(self):
        """Testa verificação com senha vazia"""
        usuario = Usuario(
            nome='Daniel Martins',
            email='daniel@example.com',
            senha='senha123',
            tipo='comprador'
        )
        
        assert usuario.verificar_senha('') is False
        assert usuario.verificar_senha(None) is False
    
    def test_verificar_e_atualizar_perfil_completo(self):
        """Testa verificação de perfil completo"""
        usuario = Usuario(
            nome='Eduarda Pereira',
            email='eduarda@example.com',
            senha='senha123',
            tipo='comprador',
            nif='123456789',
            provincia_id=1,
            municipio_id=1
        )
        
        assert usuario.verificar_e_atualizar_perfil() is True
        assert usuario.perfil_completo is True
    
    def test_verificar_perfil_produtor_sem_iban(self):
        """Testa que produtor precisa de IBAN"""
        usuario = Usuario(
            nome='Fabio Correia',
            email='fabio@example.com',
            senha='senha123',
            tipo='produtor',
            nif='123456789',
            provincia_id=1,
            municipio_id=1
            # Sem IBAN
        )
        
        assert usuario.verificar_e_atualizar_perfil() is False
    
    def test_pode_criar_anuncios_conta_validada(self):
        """Testa permissão para criar anúncios"""
        usuario = Usuario(
            nome='Gabriela Monteiro',
            email='gabriela@example.com',
            senha='senha123',
            tipo='produtor',
            conta_validada=True
        )
        
        assert usuario.pode_criar_anuncios() is True
    
    def test_pode_criar_anuncios_conta_nao_validada(self):
        """Testa que conta não validada não pode criar anúncios"""
        usuario = Usuario(
            nome='Henrique Araújo',
            email='henrique@example.com',
            senha='senha123',
            tipo='produtor',
            conta_validada=False
        )
        
        assert usuario.pode_criar_anuncios() is False
    
    def test_pode_criar_anuncios_comprador(self):
        """Testa que comprador não pode criar anúncios"""
        usuario = Usuario(
            nome='Isabela Nunes',
            email='isabela@example.com',
            senha='senha123',
            tipo='comprador',
            conta_validada=True
        )
        
        assert usuario.pode_criar_anuncios() is False
    
    def test_atualizar_saldo_decimal(self):
        """Testa atualização de saldo com Decimal"""
        usuario = Usuario(
            nome='Jorge Ramos',
            email='jorge@example.com',
            senha='senha123',
            tipo='comprador',
            saldo_disponivel=Decimal('100.00')
        )
        
        usuario.atualizar_saldo(Decimal('50.00'))
        assert usuario.saldo_disponivel == Decimal('150.00')
    
    def test_atualizar_saldo_float(self):
        """Testa conversão automática de float para Decimal"""
        usuario = Usuario(
            nome='Kelly Barbosa',
            email='kelly@example.com',
            senha='senha123',
            tipo='comprador',
            saldo_disponivel=Decimal('100.00')
        )
        
        usuario.atualizar_saldo(50.00)
        assert usuario.saldo_disponivel == Decimal('150.00')
    
    def test_to_dict(self):
        """Testa serialização para dicionário"""
        usuario = Usuario(
            id=1,
            nome='Leonardo Cardoso',
            telemovel='923456789',
            email='leonardo@example.com',
            tipo='produtor',
            perfil_completo=True,
            conta_validada=True,
            saldo_disponivel=Decimal('500.00'),
            vendas_concluidas=10,
            data_cadastro=datetime.now(timezone.utc)
        )
        
        data_dict = usuario.to_dict()
        
        assert data_dict['id'] == 1
        assert data_dict['nome'] == 'Leonardo Cardoso'
        assert data_dict['email'] == 'leonardo@example.com'
        assert data_dict['tipo'] == 'produtor'
        assert data_dict['perfil_completo'] is True
        assert data_dict['conta_validada'] is True
        assert data_dict['saldo_disponivel'] == 500.0
        assert data_dict['vendas_concluidas'] == 10
        assert 'data_cadastro' in data_dict


class TestUsuarioRelacionamentos:
    """Testes de relacionamentos do Usuario"""
    
    def test_notificacoes_nao_lidas(self, app):
        """Testa contagem de notificações não lidas"""
        with app.app_context():
            usuario = Usuario(
                nome='Mariana Teixeira',
                telemovel='923456780',
                email='mariana@example.com',
                senha='senha123',
                tipo='comprador'
            )
            db.session.add(usuario)
            db.session.commit()
            
            # Criar notificações
            from app.models import Notificacao
            
            for i in range(5):
                notificacao = Notificacao(
                    usuario_id=usuario.id,
                    mensagem=f'Mensagem {i}',
                    lida=(i < 2)  # Primeiras 2 lidas
                )
                db.session.add(notificacao)
            
            db.session.commit()
            
            # Recarregar relacionamentos
            db.session.refresh(usuario)
            
            assert usuario.notificacoes_nao_lidas() == 3
    
    def test_ultimas_notificacoes(self, app):
        """Testa obtenção das últimas notificações"""
        with app.app_context():
            usuario = Usuario(
                nome='Nuno Ribeiro',
                telemovel='923456781',
                email='nuno@example.com',
                senha='senha123',
                tipo='comprador'
            )
            db.session.add(usuario)
            db.session.commit()
            
            from app.models import Notificacao
            
            # Criar 10 notificações
            for i in range(10):
                notificacao = Notificacao(
                    usuario_id=usuario.id,
                    mensagem=f'Mensagem {i}'
                )
                db.session.add(notificacao)
            
            db.session.commit()
            db.session.refresh(usuario)
            
            ultimas = usuario.ultimas_notificacoes(limite=5)
            assert len(ultimas) == 5
    
    def test_obter_carteira_nova(self, session):
        """Testa criação de nova carteira"""
        usuario = Usuario(
            nome='Olivia Pinto',
            telemovel='923456782',
            email='olivia@example.com',
            senha='senha123',
            tipo='produtor'
        )
        session.add(usuario)
        session.commit()
        
        carteira = usuario.obter_carteira()
        
        assert carteira is not None
        assert carteira.usuario_id == usuario.id
        assert carteira.saldo_disponivel == Decimal('0.00')
    
    def test_obter_carteira_existente(self, session):
        """Testa obtenção de carteira existente"""
        from app.models import Carteira
        
        usuario = Usuario(
            nome='Paulo Medeiros',
            telemovel='923456783',
            email='paulo@example.com',
            senha='senha123',
            tipo='produtor'
        )
        session.add(usuario)
        session.commit()
        
        # Criar carteira
        carteira = Carteira(
            usuario_id=usuario.id,
            saldo_disponivel=Decimal('1000.00')
        )
        session.add(carteira)
        session.commit()
        
        carteira_obtida = usuario.obter_carteira()
        assert carteira_obtida.id == carteira.id
        assert carteira_obtida.saldo_disponivel == Decimal('1000.00')


# Marcador de integração (comentado para evitar erro)
# @pytest.mark.integration
class TestUsuarioIntegracao:
    """Testes de integração do Usuario"""
    
    def test_criar_usuario_completo(self, session):
        """Testa criação de usuário com todos os dados"""
        provincia = Provincia(nome='Luanda')
        municipio = Municipio(nome='Belas', provincia=provincia)
        
        usuario = Usuario(
            nome='Quitéria Gomes',
            telemovel='923456792',  # Alterado para evitar conflito
            email='quiteria@example.com',
            tipo='produtor',
            nif='123456789',
            iban='AO06.0000.0000.0000.0000.0',
            provincia=provincia,
            municipio=municipio,
            conta_validada=True
        )
        
        usuario.set_senha('SenhaForte123!')
        
        session.add(provincia)
        session.add(municipio)
        session.add(usuario)
        session.commit()
        
        # Verificar perfil completo após configurar todos os dados
        assert usuario.verificar_e_atualizar_perfil() is True
        assert usuario.perfil_completo is True
        assert usuario.pode_criar_anuncios() is True
    
    def test_usuario_constraints_unicos(self, session):
        """Testa constraints únicos de email e telemóvel"""
        from sqlalchemy.exc import IntegrityError
        
        usuario1 = Usuario(
            nome='Roberto Alves',
            telemovel='923456793',  # Alterado para evitar conflito
            email='roberto@example.com',
            senha='senha123',
            tipo='comprador'
        )
        
        session.add(usuario1)
        session.commit()
        
        # Tentar criar outro usuário com mesmo email
        usuario2 = Usuario(
            nome='Outro Usuário',
            telemovel='933333333',
            email='roberto@example.com',  # Mesmo email
            senha='senha123',
            tipo='comprador'
        )
        
        session.add(usuario2)
        with pytest.raises(IntegrityError):
            session.commit()
        
        session.rollback()
        
        # Tentar criar outro usuário com mesmo telemóvel
        usuario3 = Usuario(
            nome='Terceiro Usuário',
            telemovel='923456793',  # Mesmo telemóvel que usuario1
            email='terceiro@example.com',
            senha='senha123',
            tipo='comprador'
        )
        
        session.add(usuario3)
        with pytest.raises(IntegrityError):
            session.commit()
