"""
API para Cadastro de Produtores - Fluxo Next.js
"""
from flask import Blueprint, jsonify, request, session, current_app
from app.extensions import db
from app.models import Usuario, Provincia, Municipio
from app.services.otp_service import gerar_e_enviar_otp, reenviar_otp, OTPService
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)
api_cadastro_bp = Blueprint('api_cadastro', __name__, url_prefix='/api/cadastro')


@api_cadastro_bp.route('/iniciar', methods=['POST'])
def iniciar_cadastro():
    """
    API: Iniciar cadastro de produtor
    Valida telemóvel e envia OTP
    """
    try:
        data = request.get_json()
        telemovel = data.get('telemovel', '').strip()
        
        # Validação básica
        if not telemovel or not telemovel.startswith('9') or len(telemovel) != 9:
            return jsonify({
                'success': False,
                'message': 'Número inválido. Deve começar com 9 e ter 9 dígitos'
            }), 400
        
        # Verificar duplicidade
        if Usuario.query.filter_by(telemovel=telemovel).first():
            return jsonify({
                'success': False,
                'message': 'Este número já possui conta na AgroKongo'
            }), 409
        
        # Gerar e enviar OTP
        resultado = gerar_e_enviar_otp(
            telemovel=telemovel,
            canal='whatsapp',
            ip_address=request.remote_addr
        )
        
        if resultado['sucesso']:
            # Armazenar na sessão
            session['cadastro_telemovel'] = telemovel
            session['cadastro_canal'] = 'whatsapp'
            
            return jsonify({
                'success': True,
                'message': 'Código enviado com sucesso!'
            })
        else:
            return jsonify({
                'success': False,
                'message': resultado['mensagem']
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao iniciar cadastro: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao conectar com servidor'
        }), 500


@api_cadastro_bp.route('/verificar-otp', methods=['POST'])
def verificar_otp():
    """
    API: Verificar código OTP
    """
    try:
        data = request.get_json()
        telemovel = data.get('telemovel', '').strip()
        otp = data.get('otp', '').strip()
        
        # Validar dados
        if not telemovel or not otp or len(otp) != 6:
            return jsonify({
                'success': False,
                'message': 'Dados inválidos'
            }), 400
        
        # Verificar se telemóvel está na sessão
        if session.get('cadastro_telemovel') != telemovel:
            return jsonify({
                'success': False,
                'message': 'Sessão inválida. Comece novamente'
            }), 401
        
        # Validar OTP
        resultado = OTPService.validar_otp(
            telemovel=telemovel,
            codigo_informado=otp,
            ip_address=request.remote_addr
        )
        
        if resultado['valido']:
            return jsonify({
                'success': True,
                'message': 'Código verificado com sucesso!'
            })
        else:
            status_code = 400 if resultado['tentativas_restantes'] > 0 else 429
            return jsonify({
                'success': False,
                'message': resultado['mensagem'],
                'tentativas_restantes': resultado['tentativas_restantes']
            }), status_code
            
    except Exception as e:
        logger.error(f"Erro ao verificar OTP: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao conectar com servidor'
        }), 500


@api_cadastro_bp.route('/reenviar-otp', methods=['POST'])
def reenviar_otp_api():
    """
    API: Reenviar código OTP
    """
    try:
        data = request.get_json()
        telemovel = data.get('telemovel', '').strip()
        
        # Verificar sessão
        if session.get('cadastro_telemovel') != telemovel:
            return jsonify({
                'success': False,
                'message': 'Sessão inválida'
            }), 401
        
        canal = session.get('cadastro_canal', 'whatsapp')
        resultado = reenviar_otp(telemovel, canal, request.remote_addr)
        
        if resultado['sucesso']:
            return jsonify({
                'success': True,
                'message': 'Novo código enviado!'
            })
        else:
            return jsonify({
                'success': False,
                'message': resultado['mensagem']
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao reenviar OTP: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao conectar com servidor'
        }), 500


@api_cadastro_bp.route('/provincias', methods=['GET'])
def listar_provincias():
    """
    API: Listar províncias de Angola
    """
    try:
        provincias = Provincia.query.order_by(Provincia.nome).all()
        
        return jsonify({
            'success': True,
            'data': [
                {
                    'id': p.id,
                    'nome': p.nome,
                    'municipios': [
                        {'id': m.id, 'nome': m.nome}
                        for m in p.municipios
                    ]
                }
                for p in provincias
            ]
        })
    except Exception as e:
        logger.error(f"Erro ao listar províncias: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao carregar províncias'
        }), 500


@api_cadastro_bp.route('/finalizar', methods=['POST'])
def finalizar_cadastro():
    """
    API: Finalizar cadastro
    Cria conta e redireciona para dashboard
    """
    try:
        data = request.get_json()
        telemovel = data.get('telemovel', '').strip()
        
        # Verificar sessão
        if session.get('cadastro_telemovel') != telemovel:
            return jsonify({
                'success': False,
                'message': 'Sessão inválida'
            }), 401
        
        # TODO: Implementar criação completa da conta aqui
        # Por enquanto, apenas retorna sucesso
        
        return jsonify({
            'success': True,
            'message': 'Cadastro finalizado com sucesso!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao finalizar cadastro: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao conectar com servidor'
        }), 500
