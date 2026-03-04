"""
Rotas API para Conformidade LGPD (Lei de Proteção de Dados de Angola)
Inclui endpoints para consentimento, exportação e exclusão de dados
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db, csrf
from app.models.lgpd import ConsentimentoLGPD, RegistroAnonimizacao
from app.utils.encryption import get_client_ip
import hashlib
from datetime import datetime, timezone

lgpd_bp = Blueprint('lgpd', __name__, url_prefix='/api/lgpd')

# Versão atual dos documentos de consentimento
VERSAO_TERMOS = '1.0'
VERSAO_PRIVACIDADE = '1.0'


@lgpd_bp.route('/consentimento', methods=['POST'])
@csrf.exempt
@login_required
def registrar_consentimento():
    """
    Registra consentimento do utilizador para processamento de dados.
    
    Body JSON:
    {
        "tipo": "termos_uso|privacidade|marketing|dados_financeiros|compartilhamento_terceiros",
        "consentido": true|false,
        "versao": "1.0"
    }
    """
    data = request.get_json(silent=True)
    
    if not data:
        return jsonify({'erro': 'Dados não fornecidos'}), 400
    
    tipo = data.get('tipo')
    consentido = data.get('consentido')
    versao = data.get('versao')
    
    # Validar tipo de consentimento
    tipos_validos = [
        'termos_uso', 
        'privacidade', 
        'marketing', 
        'dados_financeiros', 
        'compartilhamento_terceiros'
    ]
    
    if tipo not in tipos_validos:
        return jsonify({
            'erro': f'Tipo de consentimento inválido. Valores válidos: {tipos_validos}'
        }), 400
    
    if consentido is None:
        return jsonify({'erro': 'Campo "consentido" é obrigatório'}), 400
    
    # Determinar versão
    if tipo == 'termos_uso':
        versao = versao or VERSAO_TERMOS
    elif tipo == 'privacidade':
        versao = versao or VERSAO_PRIVACIDADE
    
    try:
        if consentido:
            # Registrar novo consentimento
            ConsentimentoLGPD.registrar_consentimento(
                usuario_id=current_user.id,
                tipo=tipo,
                versao=versao,
                ip_address=get_client_ip(request),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.commit()
            
            return jsonify({
                'mensagem': f'Consentimento para {tipo} registrado com sucesso',
                'tipo': tipo,
                'versao': versao,
                'consentido': True
            }), 200
        else:
            # Revogar consentimento existente
            consentimento = ConsentimentoLGPD.query.filter_by(
                usuario_id=current_user.id,
                tipo=tipo,
                consentido=True
            ).first()
            
            if consentimento:
                consentimento.revogar(data.get('motivo', 'Revogação pelo utilizador'))
                db.session.commit()
            
            return jsonify({
                'mensagem': f'Consentimento para {tipo} revogado com sucesso',
                'tipo': tipo,
                'consentido': False
            }), 200
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@lgpd_bp.route('/consentimentos', methods=['GET'])
@login_required
def listar_consentimentos():
    """
    Lista todos os consentimentos do utilizador atual.
    """
    consentimentos = ConsentimentoLGPD.query.filter_by(
        usuario_id=current_user.id
    ).order_by(ConsentimentoLGPD.data_consentimento.desc()).all()
    
    return jsonify({
        'consentimentos': [{
            'tipo': c.tipo,
            'versao': c.versao_documento,
            'consentido': c.consentido,
            'data_consentimento': c.data_consentimento.isoformat() if c.data_consentimento else None,
            'data_revogacao': c.data_revogacao.isoformat() if c.data_revogacao else None
        } for c in consentimentos]
    }), 200


@lgpd_bp.route('/consentimento/<tipo>', methods=['GET'])
@login_required
def verificar_consentimento(tipo):
    """
    Verifica se o utilizador deu consentimento para um tipo específico.
    """
    has_consent = ConsentimentoLGPD.verificar_consentimento(
        usuario_id=current_user.id,
        tipo=tipo
    )
    
    return jsonify({
        'tipo': tipo,
        'consentido': has_consent
    }), 200


@lgpd_bp.route('/exportar-dados', methods=['GET'])
@login_required
def exportar_dados():
    """
    Exporta todos os dados pessoais do utilizador (Portabilidade de Dados - Art. 18 LPDP).
    """
    from app.models import Usuario, Transacao, Safra, Notificacao, Carteira
    
    usuario = Usuario.query.get(current_user.id)
    
    # Coletar todos os dados
    dados = {
        'usuario': {
            'id': usuario.id,
            'nome': usuario.nome,
            'telemovel': usuario.telemovel,
            'email': usuario.email,
            'tipo': usuario.tipo,
            'data_cadastro': usuario.data_cadastro.isoformat() if usuario.data_cadastro else None,
            'provincia': usuario.provincia.nome if usuario.provincia else None,
            'municipio': usuario.municipio.nome if usuario.municipio else None,
        },
        'transacoes': [{
            'id': t.id,
            'status': t.status,
            'valor': float(t.valor_total) if t.valor_total else 0,
            'data_criacao': t.data_criacao.isoformat() if t.data_criacao else None
        } for t in usuario.transacoes_como_comprador + usuario.transacoes_como_vendedor],
        'safras': [{
            'id': s.id,
            'nome': s.nome,
            'quantidade': float(s.quantidade) if s.quantidade else 0,
            'preco_kg': float(s.preco_kg) if s.preco_kg else 0
        } for s in usuario.safras_criadas],
        'notificacoes': [{
            'id': n.id,
            'mensagem': n.mensagem,
            'lida': n.lida,
            'data_criacao': n.data_criacao.isoformat() if n.data_criacao else None
        } for n in usuario.notificacoes],
        'carteira': {
            'saldo_disponivel': float(usuario.saldo_disponivel) if usuario.saldo_disponivel else 0
        } if hasattr(usuario, 'saldo_disponivel') else None,
        'consentimentos': [{
            'tipo': c.tipo,
            'consentido': c.consentido,
            'data': c.data_consentimento.isoformat() if c.data_consentimento else None
        } for c in usuario.consentimentos],
        'data_exportacao': datetime.now(timezone.utc).isoformat(),
        'versao': '1.0'
    }
    
    return jsonify(dados), 200


@lgpd_bp.route('/solicitar-exclusao', methods=['POST'])
@csrf.exempt
@login_required
def solicitar_exclusao():
    """
    Solicita a exclusão/anonymização dos dados pessoais (Direito ao Esquecimento - Art. 18 LPDP).
    """
    data = request.get_json() or {}
    motivo = data.get('motivo', 'Solicitação do utilizador')
    
    # Verificar se há consentimento para termos de uso
    if not ConsentimentoLGPD.verificar_consentimento(current_user.id, 'termos_uso'):
        return jsonify({
            'erro': 'Não é possível processar a solicitação. Consentimento aos termos de uso é necessário.'
        }), 400
    
    try:
        # Criar registro de anonimização
        # Nota: A anonimização real deve ser feita por um processo assíncrono/admin
        hash_anonimizacao = hashlib.sha256(
            f"{current_user.id}_{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()
        
        registro = RegistroAnonimizacao(
            usuario_id=current_user.id,
            dados_anonimizados=['nome', 'telemovel', 'email', 'iban', 'nif'],
            hash_anonimizacao=hash_anonimizacao,
            motivo=motivo,
            solicitado_por='usuario'
        )
        
        db.session.add(registro)
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Solicitação de exclusão registrada. Os dados serão anonimizados em até 30 dias.',
            'solicitacao_id': registro.id,
            'hash_verificacao': hash_anonimizacao,
            'prazo': '30 dias'
        }), 202
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@lgpd_bp.route('/politica-privacidade', methods=['GET'])
def obter_politica_privacidade():
    """
    Retorna a política de privacidade atual.
    """
    return jsonify({
        'versao': VERSAO_PRIVACIDADE,
        'data_atualizacao': '2026-03-02',
        'principios': [
            'Transparência no tratamento de dados',
            'Minimização de dados coletados',
            'Finalidade específica para cada tratamento',
            'Direito de acesso e correção',
            'Direito ao esquecimento',
            'Portabilidade de dados'
        ],
        'dados_coletados': [
            'Dados de identificação (nome, email, telemóvel)',
            'Dados de localização (provincia, município)',
            'Dados financeiros (NIF, IBAN - criptografados)',
            'Dados de transações e safras'
        ],
        'bases_legais': [
            'Consentimento do titular',
            'Execução de contrato',
            'Obrigação legal',
            'Legítimo interesse'
        ],
        'contacto_dpo': 'dpo@agrokongo.ao'
    }), 200
