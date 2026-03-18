"""
Testes de Integração da API RESTful
Testa endpoints da API para frontend mobile/React.
"""
import pytest
import json
from decimal import Decimal

from app.extensions import db
from app.models import Usuario, Safra, Produto, Provincia, Municipio, TransactionStatus
from app.utils.status_helper import status_to_value


class TestApiProdutos:
    """Testa endpoints de produtos."""
    
    def test_listar_produtos_vazio(self, client, app):
        """Testa listagem de produtos quando não há nenhum."""
        with app.app_context():
            response = client.get('/api/v1/produtos')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert 'data' in data
            assert isinstance(data['data'], list)
    
    def test_listar_produtos_com_dados(self, client, app):
        """Testa listagem com produtos cadastrados."""
        with app.app_context():
            # Criar produtos
            produtos = [
                Produto(nome='Milho', categoria='Cereais'),
                Produto(nome='Mandioca', categoria='Raízes'),
                Produto(nome='Feijão', categoria='Leguminosas')
            ]
            db.session.add_all(produtos)
            db.session.commit()
            
            response = client.get('/api/v1/produtos')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert len(data['data']) == 3
            
            # Verificar estrutura dos dados
            primeiro = data['data'][0]
            assert 'id' in primeiro
            assert 'nome' in primeiro
            assert 'categoria' in primeiro


class TestApiSafras:
    """Testa endpoints de safras."""
    
    @pytest.fixture
    def setup_safra_teste(self, app, db):
        """Cria safras para testes."""
        # Nao usar with app.app_context() para manter sessao ativa
        # Criar localização
        prov = Provincia(nome='Luanda')
        db.session.add(prov)
        db.session.flush()
        
        mun = Municipio(nome='Belas', provincia_id=prov.id)
        db.session.add(mun)
        db.session.flush()
        
        # Criar produtor
        produtor = Usuario(
            nome="Teste Produtor",
            telemovel="923000001",
            email="produtor@api.com",
            tipo="produtor",
            municipio_id=mun.id,
            provincia_id=prov.id,
            perfil_completo=True,
            conta_validada=True
        )
        produtor.senha = "123456"
        db.session.add(produtor)
        db.session.flush()
        
        # Criar produto
        produto = Produto(nome='Tomate', categoria='Hortícolas')
        db.session.add(produto)
        db.session.flush()
        
        # Criar safra
        safra = Safra(
            produtor_id=produtor.id,
            produto_id=produto.id,
            quantidade_disponivel=Decimal('500.0'),
            preco_por_unidade=Decimal('150.0'),
            status=status_to_value(TransactionStatus.PENDENTE)
        )
        db.session.add(safra)
        db.session.commit()
        
        # Retornar IDs como valores primitivos
        return {
            'safra_id': int(safra.id),
            'produtor_id': int(produtor.id),
            'provincia_id': int(prov.id)
        }
    
    def test_listar_safras_vazio(self, client, app):
        """Testa listagem de safras vazia."""
        response = client.get('/api/v1/safras')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'safras' in data['data']
        assert 'pagination' in data['data']
    
    def test_listar_safras_com_filtro_provincia(self, client, app, setup_safra_teste):
        """Testa filtro de safras por provincia."""
        with app.app_context():
            provincia_id = setup_safra_teste['provincia_id']  # Usa ID direto
            
            response = client.get(f'/api/v1/safras?provincia={provincia_id}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert len(data['data']['safras']) >= 1
            
            # Verificar dados da safra
            safra = data['data']['safras'][0]
            assert 'produto' in safra
            assert 'preco_unitario' in safra
            assert 'produtor' in safra
    
    def test_listar_safras_com_busca(self, client, app, setup_safra_teste):
        """Testa busca textual de safras."""
        response = client.get('/api/v1/safras?q=Tomate')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        # Deve encontrar a safra de tomate
    
    def test_detalhar_safra(self, client, app, setup_safra_teste):
        """Testa detalhes de uma safra especifica."""
        with app.app_context():
            safra_id = setup_safra_teste['safra_id']  # Usa ID direto
            
            response = client.get(f'/api/v1/safras/{safra_id}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert 'produto' in data['data']
            assert 'produtor' in data['data']
            assert 'quantidade_disponivel' in data['data']
    
    def test_detalhar_safra_nao_existente(self, client, app):
        """Testa erro ao buscar safra inexistente."""
        response = client.get('/api/v1/safras/99999')
        
        # Deve retornar 404 quando a safra não existe
        assert response.status_code == 404

    def test_listar_safras_paginacao(self, client, app, setup_safra_teste):
        """Testa paginação de resultados."""
        response = client.get('/api/v1/safras?page=1&per_page=5')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'pagination' in data['data']
        
        pag = data['data']['pagination']
        assert 'page' in pag
        assert 'per_page' in pag
        assert 'total' in pag
        assert 'pages' in pag


class TestApiProvincias:
    """Testa endpoint de províncias."""
    
    def test_listar_provincias(self, client, app):
        """Testa listagem de províncias e municípios."""
        with app.app_context():
            prov = Provincia(nome='Zaire')
            db.session.add(prov)
            db.session.flush()
            
            mun1 = Municipio(nome='Mbanza Kongo', provincia_id=prov.id)
            mun2 = Municipio(nome='Nóqui', provincia_id=prov.id)
            db.session.add_all([mun1, mun2])
            db.session.commit()
            
            response = client.get('/api/v1/provincias')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert isinstance(data['data'], list)
            
            # Encontrar Zaire na lista
            zaire = next((p for p in data['data'] if p['nome'] == 'Zaire'), None)
            assert zaire is not None
            assert 'municipios' in zaire
            assert len(zaire['municipios']) == 2


class TestApiHealth:
    """Testa health check da API."""
    
    def test_health_check(self, client, app):
        """Testa endpoint de health check."""
        response = client.get('/api/v1/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'status' in data['data']
        assert 'version' in data['data']
        assert 'service' in data['data']
        assert data['data']['service'] == 'AgroKongo API'


class TestApiAutenticacao:
    """Testa endpoints de autenticação."""
    
    def test_usuario_nao_autenticado(self, client, app):
        """Testa que usuário não autenticado recebe erro."""
        response = client.get('/api/v1/auth/me')
        
        # Deve redirecionar ou retornar erro
        assert response.status_code in [302, 401]


class TestSwaggerDocs:
    """Testa documentação Swagger."""
    
    def test_swagger_json(self, client, app):
        """Testa especificação OpenAPI em JSON."""
        response = client.get('/api/docs/swagger.json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'openapi' in data
        assert 'info' in data
        assert 'paths' in data
        assert data['openapi'].startswith('3.0')
        
        # Verificar info básico
        assert data['info']['title'] == 'AgroKongo API'
        assert 'version' in data['info']
    
    def test_swagger_ui(self, client, app):
        """Testa interface Swagger UI."""
        response = client.get('/api/docs/swagger-ui.html')
        
        assert response.status_code == 200
        assert b'Swagger UI' in response.data or b'swagger-ui' in response.data
