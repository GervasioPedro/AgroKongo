# app/routes/cadastro_produtor.py - Fluxo simplificado de 3 passos
# Alinhado com frontend Next.js

from flask import Blueprint, request, session, current_app, redirect, url_for
from flask_login import login_user

from app.extensions import db
from app.models import Usuario, Provincia, Municipio, LogAuditoria, Carteira
from app.shared.constants import (
    CADASTRO_SENHA_MIN_DIGITOS,
    CADASTRO_SENHA_MAX_DIGITOS,
    IBAN_PREFIXO,
    IBAN_TAMANHO,
    AUDITORIA_ACOES
)
from app.shared.responses import success_response, error_response, validation_error
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)
cadastro_bp = Blueprint('cadastro', __name__)


@cadastro_bp.route('/criar-conta-produtor', methods=['GET'])
def criar_conta_produtor():
    """
    Redireciona para frontend Next.js
    Legacy route para compatibilidade
    """
    return redirect('http://localhost:3000/auth/cadastro/passo-1')


@cadastro_bp.route('/api/cadastro/dados-basicos', methods=['POST'])
def salvar_dados_basicos():
    """
    Passo 2: Salvar dados básicos do produtor
    Chamado pelo frontend Next.js após validação do OTP
    """
    try:
        data = request.get_json()
        
        # Validar sessão
        telemovel = session.get('cadastro_telemovel')
        if not telemovel:
            return error_response(
                message='Sessão inválida. Comece novamente.',
                status_code=401
            )
        
        # Extrair dados
        nome = data.get('nome', '').strip()
        provincia_id = data.get('provincia_id')
        municipio_id = data.get('municipio_id')
        principal_cultura = data.get('principal_cultura', '').strip()
        
        # Validações
        if not nome or len(nome) < 3:
            return validation_error(
                field='nome',
                message='Nome completo é obrigatório (mínimo 3 caracteres)'
            )
        
        if not provincia_id or not municipio_id:
            return validation_error(
                field='localizacao',
                message='Selecione província e município'
            )
        
        if not principal_cultura:
            return validation_error(
                field='principal_cultura',
                message='Informe sua principal cultura'
            )
        
        # Armazenar na sessão
        session['cadastro_dados'] = {
            'nome': nome,
            'provincia_id': int(provincia_id),
            'municipio_id': int(municipio_id),
            'principal_cultura': principal_cultura
        }
        
        return success_response(
            data=None,
            message='Dados básicos salvos com sucesso!'
        )
        
    except Exception as e:
        logger.error(f"Erro ao salvar dados básicos: {str(e)}")
        return error_response(
            message='Erro ao conectar com servidor',
            status_code=500
        )


@cadastro_bp.route('/api/cadastro/finalizar', methods=['POST'])
def finalizar_cadastro():
    """
    Passo 3: Finalizar cadastro criando usuário
    Chamado pelo frontend Next.js
    """
    try:
        data = request.get_json()
        telemovel = data.get('telemovel', '').strip()
        senha = data.get('senha', '').strip()
        iban = data.get('iban', '').strip().upper()
        
        # Validar sessão
        if session.get('cadastro_telemovel') != telemovel:
            return error_response(
                message='Sessão inválida',
                status_code=401
            )
        
        # Validar dados necessários
        dados = session.get('cadastro_dados')
        if not dados:
            return error_response(
                message='Dados incompletos. Preencha todos os campos.',
                status_code=400
            )
        
        # Validar senha (PIN 4-6 dígitos)
        if not senha or not senha.isdigit() or len(senha) < CADASTRO_SENHA_MIN_DIGITOS or len(senha) > CADASTRO_SENHA_MAX_DIGITOS:
            return validation_error(
                field='senha',
                message=f'Senha deve ser um PIN de {CADASTRO_SENHA_MIN_DIGITOS} a {CADASTRO_SENHA_MAX_DIGITOS} dígitos'
            )
        
        # Validar IBAN
        erro_iban = _validar_iban_angolano(iban)
        if erro_iban:
            return validation_error(
                field='iban',
                message=erro_iban
            )
        
        # Criar usuário
        usuario = _criar_usuario_produtor(
            telemovel=telemovel,
            dados=dados,
            senha=senha,
            iban=iban
        )
        
        # Limpar sessão
        for key in ['cadastro_telemovel', 'cadastro_dados', 'cadastro_canal']:
            session.pop(key, None)
        
        # Login automático
        login_user(usuario)
        
        logger.info(f"Produtor criado com sucesso: {usuario.nome} (ID: {usuario.id})")
        
        return success_response(
            data={'redirect': url_for('produtor.dashboard')},
            message='Cadastro realizado com sucesso! Bem-vindo ao AgroKongo.'
        )
        
    except Exception as e:
        logger.error(f"Erro ao finalizar cadastro: {str(e)}")
        return error_response(
            message='Erro ao criar conta. Tente novamente.',
            status_code=500
        )


def _validar_iban_angolano(iban):
    """Valida formato do IBAN angolano. Retorna mensagem de erro ou None."""
    if not iban:
        return 'IBAN é obrigatório.'
    
    if not iban.startswith(IBAN_PREFIXO) or len(iban) != IBAN_TAMANHO:
        return f'IBAN inválido. Use formato {IBAN_PREFIXO} + {IBAN_TAMANHO - len(IBAN_PREFIXO)} dígitos.'
    
    if not iban[len(IBAN_PREFIXO):].isdigit():
        return 'IBAN inválido. Verifique os dígitos.'
    
    return None


def _criar_usuario_produtor(telemovel: str, dados: dict, senha: str, iban: str) -> Usuario:
    """
    RN02: Criação do usuário e carteira de forma atômica
    """
    try:
        # Iniciar transação atômica
        db.session.begin_nested()
        
        # Criar usuário
        usuario = Usuario(
            nome=dados['nome'],
            telemovel=telemovel,
            tipo='produtor',
            provincia_id=dados['provincia_id'],
            municipio_id=dados['municipio_id'],
            iban=iban,
            perfil_completo=True,
            conta_validada=False
        )
        usuario.set_senha(senha)
        
        db.session.add(usuario)
        db.session.flush()
        
        # RN02: Criar carteira
        carteira = Carteira(
            usuario_id=usuario.id,
            saldo_disponivel=Decimal('0.00'),
            saldo_bloqueado=Decimal('0.00')
        )
        
        db.session.add(carteira)
        
        # Log de auditoria
        db.session.add(LogAuditoria(
            usuario_id=usuario.id,
            acao=AUDITORIA_ACOES['CADASTRO_PRODUTOR'],
            detalhes=f"Produtor cadastrado: {dados['nome']} | Status: PENDENTE_VERIFICACAO"
        ))
        
        # Commit
        db.session.commit()
        
        return usuario
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro na criação do produtor: {e}")
        raise e
