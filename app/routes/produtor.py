from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from app.models import Safra, Produto, Transacao, Notificacao, TransactionStatus, AlertaPreferencia
from app.extensions import db
from app.utils.helpers import salvar_ficheiro
from functools import wraps
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from sqlalchemy import func, case
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError, OperationalError

produtor_bp = Blueprint('produtor', __name__)

# --- DECORATOR DE SEGURANÇA ---
def produtor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != 'produtor':
            if request.path.startswith('/api/'):
                return jsonify({'ok': False, 'message': 'Acesso restrito a produtores.'}), 403
            flash("Acesso restrito a produtores validados.", "danger")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== API ENDPOINTS (JSON) ====================

@produtor_bp.route('/api/produtor/dashboard', methods=['GET'])
@login_required
@produtor_required
def api_dashboard_produtor():
    # ... (código existente sem alterações)
    stats = db.session.query(
        func.sum(case((Transacao.status == TransactionStatus.FINALIZADO, Transacao.valor_liquido_vendedor), else_=0)),
        func.sum(case((Transacao.status.in_([TransactionStatus.ESCROW, TransactionStatus.ENVIADO]),
                       Transacao.valor_liquido_vendedor), else_=0)),
        func.sum(case((Transacao.status == TransactionStatus.ENTREGUE, Transacao.valor_liquido_vendedor), else_=0))
    ).filter(Transacao.vendedor_id == current_user.id).first()

    base_query = Transacao.query.options(
        joinedload(Transacao.safra).joinedload(Safra.produto)
    ).filter(Transacao.vendedor_id == current_user.id)

    reservas = base_query.filter(Transacao.status == TransactionStatus.PENDENTE) \
        .order_by(Transacao.data_criacao.desc()).limit(20).all()

    vendas = base_query.filter(Transacao.status.in_([
        TransactionStatus.AGUARDANDO_PAGAMENTO,
        TransactionStatus.ANALISE,
        TransactionStatus.ESCROW,
        TransactionStatus.ENVIADO
    ])).order_by(Transacao.data_criacao.desc()).limit(20).all()

    historico = base_query.filter(Transacao.status.in_([
        TransactionStatus.ENTREGUE,
        TransactionStatus.FINALIZADO,
        TransactionStatus.CANCELADO
    ])).order_by(Transacao.data_criacao.desc()).limit(20).all()

    def transacao_to_dict(t: Transacao):
        return {
            'id': t.id,
            'fatura_ref': t.fatura_ref,
            'status': t.status,
            'produto': getattr(getattr(t.safra, 'produto', None), 'nome', None),
            'quantidade': float(t.quantidade_comprada) if t.quantidade_comprada is not None else None,
            'valor': float(t.valor_total_pago) if t.valor_total_pago is not None else None,
            'data': t.data_criacao.isoformat() if getattr(t, 'data_criacao', None) else None
        }

    return jsonify({
        'kpis': {
            'receita_total': float(stats[0] or 0),
            'em_custodia': float(stats[1] or 0),
            'a_liquidar': float(stats[2] or 0),
            'disponivel': float(getattr(current_user, 'saldo_disponivel', 0) or 0)
        },
        'listas': {
            'reservas': [transacao_to_dict(t) for t in reservas],
            'ativas': [transacao_to_dict(t) for t in vendas],
            'historico': [transacao_to_dict(t) for t in historico]
        },
        'perfil': {
            'conta_validada': bool(getattr(current_user, 'conta_validada', False)),
            'perfil_completo': bool(getattr(current_user, 'perfil_completo', False))
        }
    })


@produtor_bp.route('/api/produtor/minhas-safras', methods=['GET'])
@login_required
@produtor_required
def api_minhas_safras():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    
    query = Safra.query.options(
        joinedload(Safra.produto),
        joinedload(Safra.produtor)
    ).filter_by(produtor_id=current_user.id).order_by(Safra.id.desc())
    
    paginated_safras = query.paginate(page=page, per_page=per_page, error_out=False)
    safras = paginated_safras.items
    
    return jsonify({
        'ok': True, 
        'safras': [s.to_dict() for s in safras],
        'pagination': {
            'page': paginated_safras.page,
            'per_page': paginated_safras.per_page,
            'total_pages': paginated_safras.pages,
            'total_items': paginated_safras.total
        }
    })

@produtor_bp.route('/api/produtor/minhas-safras', methods=['POST'])
@login_required
@produtor_required
def api_criar_safra():
    if not current_user.conta_validada:
        return jsonify({'ok': False, 'message': 'A sua conta precisa de ser validada para publicar.'}), 403
    
    data = request.form
    try:
        nova_safra = Safra(
            produtor_id=current_user.id,
            produto_id=int(data.get('produto_id')),
            quantidade_disponivel=Decimal(data.get('quantidade_disponivel', '0').replace(',', '.')),
            preco_por_unidade=Decimal(data.get('preco_por_unidade', '0').replace(',', '.')),
            descricao=data.get('descricao', ''),
            status='disponivel'
        )
        if 'imagem' in request.files:
            imagem_file = request.files['imagem']
            if imagem_file.filename != '':
                nome_foto = salvar_ficheiro(imagem_file, subpasta='safras', privado=False)
                nova_safra.imagem_url = nome_foto
        
        db.session.add(nova_safra)
        db.session.commit()
        return jsonify({'ok': True, 'safra': nova_safra.to_dict(), 'message': 'Safra criada com sucesso!'}), 201
    except (ValueError, TypeError, InvalidOperation) as e:
        db.session.rollback()
        current_app.logger.warning(f"API Criar Safra - Dados inválidos: {e}")
        return jsonify({'ok': False, 'message': 'Dados de formulário inválidos.'}), 400
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"API Criar Safra - Erro de integridade: {e}")
        return jsonify({'ok': False, 'message': 'Erro ao guardar dados. Verifique se o produto existe.'}), 409
    except OperationalError as e:
        db.session.rollback()
        current_app.logger.critical(f"API Criar Safra - Erro de DB: {e}")
        return jsonify({'ok': False, 'message': 'Erro de comunicação com a base de dados.'}), 503
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API Criar Safra - Erro inesperado: {e}")
        return jsonify({'ok': False, 'message': 'Ocorreu um erro inesperado.'}), 500


@produtor_bp.route('/api/produtor/minhas-safras/<int:id>', methods=['PUT'])
@login_required
@produtor_required
def api_atualizar_safra(id):
    safra = Safra.query.filter_by(id=id, produtor_id=current_user.id).first_or_404()
    data = request.form
    try:
        safra.produto_id = int(data.get('produto_id', safra.produto_id))
        safra.quantidade_disponivel = Decimal(data.get('quantidade_disponivel', safra.quantidade_disponivel).replace(',', '.'))
        safra.preco_por_unidade = Decimal(data.get('preco_por_unidade', safra.preco_por_unidade).replace(',', '.'))
        safra.descricao = data.get('descricao', safra.descricao)
        safra.status = data.get('status', safra.status)

        if 'imagem' in request.files:
            imagem_file = request.files['imagem']
            if imagem_file.filename != '':
                nome_foto = salvar_ficheiro(imagem_file, subpasta='safras', privado=False)
                safra.imagem_url = nome_foto

        db.session.commit()
        return jsonify({'ok': True, 'safra': safra.to_dict(), 'message': 'Safra atualizada com sucesso!'})
    except (ValueError, TypeError, InvalidOperation) as e:
        db.session.rollback()
        current_app.logger.warning(f"API Atualizar Safra - Dados inválidos: {e}")
        return jsonify({'ok': False, 'message': 'Dados de formulário inválidos.'}), 400
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"API Atualizar Safra - Erro de integridade: {e}")
        return jsonify({'ok': False, 'message': 'Erro ao guardar dados.'}), 409
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API Atualizar Safra {id} - Erro inesperado: {e}")
        return jsonify({'ok': False, 'message': 'Ocorreu um erro inesperado.'}), 500

@produtor_bp.route('/api/produtor/minhas-safras/<int:id>', methods=['DELETE'])
@login_required
@produtor_required
def api_eliminar_safra(id):
    safra = Safra.query.filter_by(id=id, produtor_id=current_user.id).first_or_404()
    
    transacoes_ativas = Transacao.query.filter(Transacao.safra_id == id, Transacao.status != 'CANCELADO').first()
    if transacoes_ativas:
        return jsonify({'ok': False, 'message': 'Não é possível eliminar uma safra com pedidos ativos ou finalizados.'}), 409

    try:
        db.session.delete(safra)
        db.session.commit()
        return jsonify({'ok': True, 'message': 'Safra eliminada com sucesso.'})
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"API Eliminar Safra - Erro de integridade: {e}")
        return jsonify({'ok': False, 'message': 'Não foi possível eliminar. Verifique as dependências.'}), 409
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API Eliminar Safra {id} - Erro inesperado: {e}")
        return jsonify({'ok': False, 'message': 'Ocorreu um erro inesperado.'}), 500

@produtor_bp.route('/api/produtor/aceitar-reserva/<int:trans_id>', methods=['POST'])
@login_required
@produtor_required
def api_aceitar_reserva(trans_id):
    try:
        venda = Transacao.query.options(
            joinedload(Transacao.safra).joinedload(Safra.produto)
        ).filter_by(id=trans_id).with_for_update().first_or_404()

        if venda.vendedor_id != current_user.id:
            return jsonify({'ok': False, 'message': 'Acesso não permitido.'}), 403
        if venda.status != TransactionStatus.PENDENTE:
            return jsonify({'ok': False, 'message': 'Esta reserva já foi processada.'}), 409
        
        venda.status = TransactionStatus.AGUARDANDO_PAGAMENTO
        db.session.add(Notificacao(
            usuario_id=venda.comprador_id,
            mensagem=f"✅ Pedido de {venda.safra.produto.nome} aceite! Pode proceder ao pagamento.",
            link=url_for('comprador.dashboard')
        ))
        db.session.commit()
        return jsonify({'ok': True, 'message': 'Reserva aceite com sucesso!'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO API ACEITAR RESERVA: {e}")
        return jsonify({'ok': False, 'message': 'Erro ao processar aceitação.'}), 500

@produtor_bp.route('/api/produtor/recusar-reserva/<int:trans_id>', methods=['POST'])
@login_required
@produtor_required
def api_recusar_reserva(trans_id):
    try:
        venda = Transacao.query.options(
            joinedload(Transacao.safra).joinedload(Safra.produto)
        ).filter_by(id=trans_id).with_for_update().first_or_404()

        if venda.vendedor_id != current_user.id:
            return jsonify({'ok': False, 'message': 'Acesso não permitido.'}), 403
        if venda.status != TransactionStatus.PENDENTE:
            return jsonify({'ok': False, 'message': 'Esta reserva já foi processada.'}), 409
        
        venda.safra.quantidade_disponivel += venda.quantidade_comprada # Devolve stock
        venda.status = TransactionStatus.CANCELADO
        db.session.add(Notificacao(
            usuario_id=venda.comprador_id,
            mensagem=f"❌ O seu pedido para {venda.safra.produto.nome} foi recusado pelo produtor.",
            link=url_for('comprador.dashboard')
        ))
        db.session.commit()
        return jsonify({'ok': True, 'message': 'Reserva recusada e stock reposto.'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO API RECUSAR RESERVA: {e}")
        return jsonify({'ok': False, 'message': 'Erro ao cancelar reserva.'}), 500

@produtor_bp.route('/api/produtor/minhas-vendas', methods=['GET'])
@login_required
@produtor_required
def api_minhas_vendas():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    status_filter = request.args.get('status')

    try:
        query = Transacao.query.options(
            joinedload(Transacao.safra).joinedload(Safra.produto),
            joinedload(Transacao.comprador)
        ).filter(Transacao.vendedor_id == current_user.id)

        if status_filter:
            statuses = status_filter.split(',')
            query = query.filter(Transacao.status.in_(statuses))

        paginated_vendas = query.order_by(Transacao.data_criacao.desc()).paginate(page=page, per_page=per_page, error_out=False)
        vendas = paginated_vendas.items
        
        return jsonify({
            'ok': True, 
            'vendas': [v.to_dict() for v in vendas],
            'pagination': {
                'page': paginated_vendas.page,
                'per_page': paginated_vendas.per_page,
                'total_pages': paginated_vendas.pages,
                'total_items': paginated_vendas.total
            }
        })
    except Exception as e:
        current_app.logger.error(f"Erro na API de minhas vendas: {e}")
        return jsonify({'ok': False, 'message': 'Erro ao buscar vendas.'}), 500

@produtor_bp.route('/api/produtor/venda/<int:id>', methods=['GET'])
@login_required
@produtor_required
def api_detalhes_venda(id):
    venda = Transacao.query.options(
        joinedload(Transacao.safra).joinedload(Safra.produto),
        joinedload(Transacao.comprador)
    ).filter_by(id=id, vendedor_id=current_user.id).first_or_404()
    return jsonify({'ok': True, 'venda': venda.to_dict()})

@produtor_bp.route('/api/produtor/confirmar-envio/<int:id>', methods=['POST'])
@login_required
@produtor_required
def api_confirmar_envio(id):
    try:
        transacao = Transacao.query.with_for_update().get_or_404(id)
        if transacao.vendedor_id != current_user.id:
            return jsonify({'ok': False, 'message': 'Acesso não permitido.'}), 403
        if transacao.status != TransactionStatus.ESCROW:
            return jsonify({'ok': False, 'message': 'Ação inválida. O pagamento deve ser confirmado primeiro.'}), 409

        transacao.status = TransactionStatus.ENVIADO
        transacao.data_envio = datetime.now(timezone.utc)
        if hasattr(transacao, 'calcular_janela_logistica'):
            transacao.calcular_janela_logistica()
        
        db.session.add(Notificacao(
            usuario_id=transacao.comprador_id,
            mensagem=f"🚚 Encomenda {transacao.fatura_ref} enviada! Previsão: {transacao.previsao_entrega.strftime('%d/%m') if transacao.previsao_entrega else 'Brevemente'}",
            link=url_for('comprador.dashboard')
        ))
        db.session.commit()
        return jsonify({'ok': True, 'message': 'Envio confirmado com sucesso!'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO API CONFIRMAR ENVIO: {e}")
        return jsonify({'ok': False, 'message': 'Erro ao processar o envio.'}), 500
