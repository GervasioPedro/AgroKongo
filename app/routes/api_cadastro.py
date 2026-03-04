# app/routes/api_cadastro.py - API REST para cadastro (compatível com frontend React)

from flask import Blueprint, request, jsonify, session
from app.extensions import db, csrf
from app.models import Usuario
from app.services.otp_service import gerar_e_enviar_otp, OTPService
import re

api_cadastro_bp = Blueprint('api_cadastro', __name__, url_prefix='/api/cadastro')

# Desabilitar CSRF para rotas de API
csrf.exempt(api_cadastro_bp)


@api_cadastro_bp.route('/passo-1', methods=['POST'])
def passo_1():
    """Passo 1: Validar dados e enviar OTP via SMS"""
    data = request.get_json()
    
    nome = data.get('nome', '').strip()
    telemovel = data.get('telemovel', '').strip()
    tipo = data.get('tipo', 'produtor').strip()
    provincia_id = data.get('provincia_id', '')
    municipio = data.get('municipio', '').strip()
    
    # Validações
    if not nome or len(nome) < 3:
        return jsonify({'sucesso': False, 'mensagem': 'Nome deve ter pelo menos 3 caracteres'}), 400
    
    if not telemovel.startswith('9') or len(telemovel) != 9:
        return jsonify({'sucesso': False, 'mensagem': 'Número inválido. Use 9 dígitos começando com 9'}), 400
    
    # Verificar duplicidade
    if Usuario.query.filter_by(telemovel=telemovel).first():
        return jsonify({'sucesso': False, 'mensagem': 'Este número já possui uma conta'}), 400
    
    # Gerar e enviar OTP via SMS
    resultado = gerar_e_enviar_otp(
        telemovel=telemovel,
        canal='sms',
        ip_address=request.remote_addr
    )
    
    if resultado['sucesso']:
        # Armazenar dados na sessão
        session['cadastro_telemovel'] = telemovel
        session['cadastro_nome'] = nome
        session['cadastro_tipo'] = tipo
        session['cadastro_provincia_id'] = provincia_id
        session['cadastro_municipio'] = municipio
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Código OTP enviado via SMS!'
        })
    else:
        return jsonify({
            'sucesso': False,
            'mensagem': resultado.get('mensagem', 'Erro ao enviar OTP')
        }), 500


@api_cadastro_bp.route('/passo-2', methods=['POST'])
def passo_2():
    """Passo 2: Validar OTP"""
    data = request.get_json()
    codigo = data.get('codigo', '').strip()
    
    telemovel = session.get('cadastro_telemovel')
    
    if not telemovel:
        return jsonify({'sucesso': False, 'mensagem': 'Sessão expirada'}), 400
    
    if not codigo or len(codigo) != 6:
        return jsonify({'sucesso': False, 'mensagem': 'Código deve ter 6 dígitos'}), 400
    
    # Validar OTP
    resultado = OTPService.validar_otp(
        telemovel=telemovel,
        codigo_informado=codigo,
        ip_address=request.remote_addr
    )
    
    if resultado['valido']:
        session['cadastro_otp_validado'] = True
        return jsonify({
            'sucesso': True,
            'mensagem': 'Código validado com sucesso!'
        })
    else:
        return jsonify({
            'sucesso': False,
            'mensagem': resultado.get('mensagem', 'Código inválido'),
            'tentativas_restantes': resultado.get('tentativas_restantes', 0)
        }), 400


@api_cadastro_bp.route('/passo-3', methods=['POST'])
def passo_3():
    """Passo 3: Finalizar cadastro com PIN, IBAN (produtor) e BI (opcional)"""
    from werkzeug.security import generate_password_hash
    from app.models import Carteira, StatusConta, LogAuditoria
    from app.utils.helpers import salvar_ficheiro
    from decimal import Decimal
    from flask_login import login_user
    
    # Verificar sessão
    if not session.get('cadastro_otp_validado'):
        return jsonify({'sucesso': False, 'mensagem': 'OTP não validado'}), 400
    
    tipo_usuario = session.get('cadastro_tipo', 'comprador')
    data = request.form
    pin = data.get('pin', '').strip()
    iban = data.get('iban', '').strip().upper() if data.get('iban') else None
    nif = data.get('nif', '').strip() if data.get('nif') else None
    tipo_entidade = data.get('tipo_entidade', 'singular').strip()
    bi_file = request.files.get('bi')
    
    # Validar PIN
    if not pin or not pin.isdigit() or len(pin) < 4 or len(pin) > 6:
        return jsonify({'sucesso': False, 'mensagem': 'PIN deve ter 4 a 6 dígitos'}), 400
    
    # Validar NIF obrigatório para produtor ou pessoa coletiva
    if tipo_usuario == 'produtor' or tipo_entidade == 'coletiva':
        if not nif or len(nif) < 9:
            return jsonify({'sucesso': False, 'mensagem': 'NIF obrigatório para produtores e pessoas coletivas'}), 400
    
    # Validar IBAN apenas para produtor
    if tipo_usuario == 'produtor':
        if not iban or not iban.startswith('AO06') or len(iban) != 27:
            return jsonify({'sucesso': False, 'mensagem': 'IBAN obrigatório para produtor. Use formato AO06 + 21 dígitos'}), 400
    
    try:
        # Salvar BI se fornecido
        bi_path = None
        if bi_file:
            bi_path = salvar_ficheiro(bi_file, subpasta='documentos_bi', privado=True)
        
        # Buscar município
        municipio_nome = session.get('cadastro_municipio')
        from app.models import Municipio
        municipio = Municipio.query.filter_by(
            nome=municipio_nome,
            provincia_id=int(session['cadastro_provincia_id'])
        ).first()
        
        # Criar usuário
        usuario = Usuario(
            nome=session['cadastro_nome'],
            telemovel=session['cadastro_telemovel'],
            tipo=tipo_usuario,
            provincia_id=int(session['cadastro_provincia_id']),
            municipio_id=municipio.id if municipio else None,
            nif=nif,
            iban=iban if tipo_usuario == 'produtor' else None,
            documento_pdf=bi_path,
            status_conta=StatusConta.PENDENTE_VERIFICACAO,
            perfil_completo=bool(nif),
            conta_validada=False
        )
        usuario.senha = pin
        
        db.session.add(usuario)
        db.session.flush()
        
        # Criar carteira
        carteira = Carteira(
            usuario_id=usuario.id,
            saldo_disponivel=Decimal('0.00'),
            saldo_bloqueado=Decimal('0.00')
        )
        db.session.add(carteira)
        
        # Log
        db.session.add(LogAuditoria(
            usuario_id=usuario.id,
            acao=f"CADASTRO_{tipo_usuario.upper()}",
            detalhes=f"{tipo_usuario.capitalize()} ({tipo_entidade}) cadastrado via API: {usuario.nome}"
        ))
        
        db.session.commit()
        
        # Fazer login automático
        login_user(usuario, remember=True)
        
        # Limpar sessão
        for key in ['cadastro_telemovel', 'cadastro_nome', 'cadastro_tipo', 'cadastro_provincia_id', 'cadastro_municipio', 'cadastro_otp_validado']:
            session.pop(key, None)
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Conta criada com sucesso!',
            'usuario_id': usuario.id,
            'tipo': tipo_usuario
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'sucesso': False, 'mensagem': f'Erro ao criar conta: {str(e)}'}), 500


@api_cadastro_bp.route('/reenviar-otp', methods=['POST'])
def reenviar_otp():
    """Reenviar código OTP"""
    from app.services.otp_service import reenviar_otp as reenviar
    
    telemovel = session.get('cadastro_telemovel')
    
    if not telemovel:
        return jsonify({'sucesso': False, 'mensagem': 'Sessão expirada'}), 400
    
    resultado = reenviar(telemovel, 'sms', request.remote_addr)
    
    if resultado['sucesso']:
        return jsonify({'sucesso': True, 'mensagem': 'Novo código enviado!'})
    else:
        return jsonify({'sucesso': False, 'mensagem': resultado['mensagem']}), 400
