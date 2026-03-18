from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Transacao, Safra, Usuario, TransactionStatus, Notificacao, LogAuditoria
from app.extensions import db, csrf
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
import uuid

# Blueprint para API de Transações
transacoes_api_bp = Blueprint('transacoes_api', __name__)
csrf.exempt(transacoes_api_bp) # Isentar de CSRF pois usa JWT

@transacoes_api_bp.route('/buy', methods=['POST', 'OPTIONS'])
@jwt_required()
def iniciar_compra():
    """
    Inicia uma nova transação de compra.
    Payload: { safra_id: int, quantidade: float }
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        data = request.get_json()
        comprador_id = get_jwt_identity()
        safra_id = data.get('safra_id')
        quantidade_req = data.get('quantidade')

        if not safra_id or not quantidade_req:
            return jsonify({'error': 'Safra ID e quantidade são obrigatórios'}), 400

        try:
            quantidade = Decimal(str(quantidade_req))
            if quantidade <= 0: raise ValueError
        except (InvalidOperation, ValueError):
            return jsonify({'error': 'Quantidade inválida'}), 400

        # TRANSAÇÃO ATÓMICA
        # Usamos begin_nested() para garantir rollback em caso de erro
        with db.session.begin_nested():
            # 1. Bloquear a linha da Safra para evitar Race Conditions (dois comprarem o mesmo stock)
            safra = Safra.query.with_for_update().get(safra_id)

            if not safra:
                return jsonify({'error': 'Safra não encontrada'}), 404

            # 2. Validações de Negócio
            if safra.produtor_id == comprador_id:
                return jsonify({'error': 'Não pode comprar a sua própria safra'}), 403
            
            if safra.status != 'disponivel':
                return jsonify({'error': 'Esta safra não está disponível'}), 400

            if quantidade > safra.quantidade_disponivel:
                return jsonify({
                    'error': f'Stock insuficiente. Disponível: {safra.quantidade_disponivel}kg'
                }), 400

            # 3. Calcular Valores
            valor_total = (quantidade * safra.preco_por_unidade).quantize(Decimal('0.01'))

            # 4. Criar Transação
            nova_transacao = Transacao(
                safra_id=safra.id,
                comprador_id=comprador_id,
                vendedor_id=safra.produtor_id,
                quantidade_comprada=quantidade,
                valor_total_pago=valor_total,
                status=TransactionStatus.PENDENTE
            )
            
            # 5. Abater Stock
            safra.quantidade_disponivel -= quantidade
            if safra.quantidade_disponivel == 0:
                safra.status = 'esgotado'

            db.session.add(nova_transacao)
            
            # 6. Logs e Notificações
            db.session.add(LogAuditoria(
                usuario_id=comprador_id,
                acao="COMPRA_API",
                detalhes=f"Iniciou compra {nova_transacao.fatura_ref} - {quantidade}kg"
            ))
            
            # Flush para gerar o ID da transação e Reference
            db.session.flush()

        # Commit final da transação
        db.session.commit()

        # Notificar Produtor (fora da transação crítica)
        try:
            notif = Notificacao(
                usuario_id=safra.produtor_id,
                mensagem=f"📦 Nova encomenda! {quantidade}kg de {safra.produto.nome}.",
                link=f"/dashboard/produtor"
            )
            db.session.add(notif)
            db.session.commit()
        except:
            pass # Não falhar a compra se a notificação falhar

        return jsonify({
            'success': True,
            'message': 'Reserva efetuada com sucesso!',
            'data': nova_transacao.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro Compra API: {e}")
        return jsonify({'error': 'Erro interno ao processar compra'}), 500


@transacoes_api_bp.route('/my', methods=['GET'])
@jwt_required()
def minhas_compras():
    """Lista as compras do utilizador logado."""
    try:
        user_id = get_jwt_identity()
        compras = Transacao.query.filter_by(comprador_id=user_id).order_by(Transacao.data_criacao.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [t.to_dict() for t in compras]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
