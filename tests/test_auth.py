import pytest
from app.models import Usuario
from app.extensions import db

def test_pagina_inicial(client):
    """
    Testa se a página inicial carrega com sucesso (HTTP 200).
    """
    response = client.get('/')
    assert response.status_code == 200
    # Verifica se o nome da plataforma aparece no HTML
    assert b'AgroKongo' in response.data

def test_acesso_protegido(client):
    """
    Testa se uma rota protegida redireciona para o login (HTTP 302).
    """
    response = client.get('/produtor/dashboard')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_login_invalido(client):
    """
    Testa uma tentativa de login com credenciais erradas.
    """
    response = client.post('/login', data={
        'telemovel': '900000000',
        'senha': 'errada'
    }, follow_redirects=True)
    
    # Deve permanecer na página (200) mas com mensagem de erro
    assert response.status_code == 200
    # A mensagem flash deve aparecer (atenção aos acentos em bytes)
    assert b'Credenciais inv' in response.data or b'inv\xc3\xa1lidas' in response.data

def test_registo_simples(client, app):
    """
    Testa o fluxo básico de registo de um novo utilizador.
    """
    with app.app_context():
        # Dados simulados do formulário
        dados = {
            'nome': 'Agricultor Teste',
            'telemovel': '923123456',
            'tipo': 'produtor',
            'senha': 'password123'
        }
        
        # Envia POST para registo
        response = client.post('/registo', data=dados, follow_redirects=True)
        
        # Verifica sucesso (Redirecionamento ou Dashboard)
        assert response.status_code == 200
        
        # Verifica se o utilizador foi criado na DB
        user = Usuario.query.filter_by(telemovel='923123456').first()
        assert user is not None
        assert user.nome == 'Agricultor Teste'
        assert user.tipo == 'produtor'
