"""
Blueprint de API REST para o marketplace AgroKongo.
Endpoints para frontend (Next.js), mobile e SPA.
"""
from flask import Blueprint, jsonify, request, abort, url_for, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from sqlalchemy import func, case
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone

from app.extensions import db, csrf # Importar CSRF
from app.models import Safra, Produto, Usuario, Provincia, Transacao, TransactionStatus, Notificacao, LogAuditoria
from app.utils.status_helper import status_to_value, get_status_description
from app.services.cache_service import cache_service
from app.utils.helpers import salvar_ficheiro

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# --- DESATIVAR CSRF PARA A API ---
# APIs REST usam tokens JWT, não cookies de sessão, por isso CSRF não se aplica.
csrf.exempt(api_bp)


# --- UTILITÁRIOS ---
def api_error(message, status_code=400):
    """Retorna erro padronizado."""
    return jsonify({
        'success': False,
        'error': message
    }), status_code


def api_success(data, message='Sucesso'):
    """Retorna sucesso padronizado."""
    return jsonify({
        'success': True,
        'message': message,
        'data': data
    })


# --- PRODUTOS E SAFRAS ---
@api_bp.route('/produtos', methods=['GET'])
def listar_produtos():
    """Lista todos os produtos disponíveis."""
    try:
        produtos = Produto.query.order_by(Produto.nome).all()
        data = [{
            'id': p.id,
            'nome': p.nome,
            'categoria': p.categoria
        } for p in produtos]
        
        return api_success(data)
    except Exception as e:
        return api_error(str(e), 500)


@api_bp.route('/safras', methods=['GET'])
def listar_safras():
    """
    Lista safras disponíveis com filtros opcionais.
    
    Query params:
    - provincia: ID da província
    - categoria: ID da categoria
    - q: Termo de busca
    - page: Número da página (default: 1)
    - per_page: Itens por página (default: 12)
    """
    try:
        prov_id = request.args.get('provincia', type=int)
        cat_id = request.args.get('categoria', type=int)
        termo = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        
        # TENTAR CACHE PRIMEIRO (apenas se não houver termo de busca)
        if not termo:
            cache_key_data = cache_service.get_safras_disponiveis(prov_id, cat_id)
            if cache_key_data:
                return api_success(cache_key_data)
        
        query = Safra.query.options(
            joinedload(Safra.produto),
            joinedload(Safra.produtor).joinedload(Usuario.provincia)
        ).filter(
            Safra.status == 'disponivel',
            Safra.quantidade_disponivel > 0
        )
        
        if prov_id:
            query = query.join(Usuario).filter(Usuario.provincia_id == prov_id)
        if cat_id:
            query = query.filter(Safra.produto_id == cat_id)
        if termo:
            from sqlalchemy import or_
            query = query.join(Produto).filter(
                or_(
                    Produto.nome.ilike(f'%{termo}%'),
                    Usuario.nome.ilike(f'%{termo}%')
                )
            )
        
        pagination = query.order_by(Safra.data_criacao.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        safras = []
        for safra in pagination.items:
            safras.append({
                'id': safra.id,
                'produto': safra.produto.nome,
                'categoria': safra.produto.categoria,
                'quantidade': float(safra.quantidade_disponivel),
                'preco_unitario': float(safra.preco_por_unidade),
                'preco_total': float(safra.quantidade_disponivel * safra.preco_por_unidade),
                'produtor': {
                    'id': safra.produtor.id,
                    'nome': safra.produtor.nome,
                    'provincia': safra.produtor.provincia.nome if safra.produtor.provincia else None,
                    'rating': float(safra.produtor.rating_vendedor) if safra.produtor.rating_vendedor else 0
                },
                'imagem': f'/uploads/safras/{safra.imagem}' if safra.imagem else None,
                'observacoes': safra.observacoes
            })
        
        response_data = {
            'safras': safras,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }
        
        # SALVAR NO CACHE (apenas se não houver termo de busca)
        if not termo:
            cache_service.cache_safras_disponiveis(response_data, prov_id, cat_id)
        
        return api_success(response_data)
        
    except Exception as e:
        return api_error(str(e), 500)


@api_bp.route('/safras/<int:id>', methods=['GET'])
def detalhar_safra(id):
    """Detalhes de uma safra específica."""
    try:
        safra = Safra.query.options(
            joinedload(Safra.produto),
            joinedload(Safra.produtor)
        ).get(id)
        
        if not safra:
            return api_error('Safra não encontrada', 404)
        
        if safra.status != 'disponivel' or safra.quantidade_disponivel <= 0:
            return api_error('Safra não disponível', 404)
        
        data = {
            'id': safra.id,
            'produto': {
                'id': safra.produto.id,
                'nome': safra.produto.nome,
                'categoria': safra.produto.categoria
            },
            'quantidade_disponivel': float(safra.quantidade_disponivel),
            'preco_por_unidade': float(safra.preco_por_unidade),
            'observacoes': safra.observacoes,
            'imagem': f'/uploads/safras/{safra.imagem}' if safra.imagem else None,
            'produtor': {
                'id': safra.produtor.id,
                'nome': safra.produtor.nome,
                'telemovel': safra.produtor.telemovel,
                'provincia': safra.produtor.provincia.nome if safra.produtor.provincia else None,
                'municipio': safra.produtor.municipio.nome if safra.produtor.municipio else None,
                'rating': float(safra.produtor.rating_vendedor) if safra.produtor.rating_vendedor else 0,
                'vendas_concluidas': safra.produtor.vendas_concluidas or 0
            }
        }
        
        return api_success(data)
        
    except Exception as e:
        return api_error(str(e), 500)


# --- PROVINCIAS E MUNICÍPIOS ---
@api_bp.route('/provincias', methods=['GET'])
def listar_provincias():
    """Lista todas as províncias de Angola."""
    try:
        provincias = Provincia.query.all()
        data = [{
            'id': p.id,
            'nome': p.nome,
            'municipios': [{'id': m.id, 'nome': m.nome} for m in p.municipios]
        } for p in provincias]
        
        return api_success(data)
    except Exception as e:
        return api_error(str(e), 500)


# --- AUTENTICAÇÃO E PERFIL ---
@api_bp.route('/auth/me', methods=['GET'])
@login_required
def usuario_atual():
    """Retorna dados do usuário autenticado."""
    try:
        data = {
            'id': current_user.id,
            'nome': current_user.nome,
            'email': current_user.email,
            'telemovel': current_user.telemovel,
            'tipo': current_user.tipo,
            'perfil_completo': current_user.perfil_completo,
            'conta_validada': current_user.conta_validada,
            'foto_perfil': f'/uploads/perfil/{current_user.foto_perfil}' if current_user.foto_perfil else None
        }
        
        return api_success(data)
    except Exception as e:
        return api_error(str(e), 500)


# --- DASHBOARD COMPRADOR ---
@api_bp.route('/dashboard/comprador', methods=['GET'])
@login_required
def dashboard_comprador():
    """Dados para o dashboard do comprador."""
    if current_user.tipo != 'comprador':
        return api_error('Acesso não autorizado', 403)
        
    try:
        # KPIs
        total_gasto = db.session.query(func.sum(Transacao.valor_total_pago)).filter(
            Transacao.comprador_id == current_user.id,
            Transacao.status.in_([
                status_to_value(TransactionStatus.ESCROW),
                status_to_value(TransactionStatus.ENVIADO),
                status_to_value(TransactionStatus.ENTREGUE),
                status_to_value(TransactionStatus.FINALIZADO)
            ])
        ).scalar() or 0
        
        compras_ativas_count = Transacao.query.filter(
            Transacao.comprador_id == current_user.id,
            Transacao.status != status_to_value(TransactionStatus.FINALIZADO),
            Transacao.status != status_to_value(TransactionStatus.CANCELADO)
        ).count()
        
        # Últimas Compras (Lista simplificada para o dashboard)
        ultimas_compras = Transacao.query.filter_by(comprador_id=current_user.id)\
            .order_by(Transacao.data_criacao.desc())\
            .limit(5).all()
            
        compras_data = []
        for t in ultimas_compras:
            compras_data.append({
                'id': t.id,
                'produto': t.safra.produto.nome if t.safra else 'Produto Indisponível',
                'valor': float(t.valor_total_pago or 0),
                'status': get_status_description(t.status),
                'data': t.data_criacao.isoformat()
            })
            
        return api_success({
            'kpis': {
                'total_gasto': float(total_gasto),
                'compras_ativas': compras_ativas_count
            },
            'ultimas_compras': compras_data
        })
        
    except Exception as e:
        return api_error(str(e), 500)


# --- DASHBOARD PRODUTOR ---
@api_bp.route('/dashboard/produtor', methods=['GET'])
@login_required
def dashboard_produtor():
    """Dados para o dashboard do produtor."""
    if current_user.tipo != 'produtor':
        return api_error('Acesso não autorizado', 403)
        
    try:
        # 1. KPIs Financeiros
        stats = db.session.query(
            # Receita Total: Transações FINALIZADAS
            func.sum(case((Transacao.status == status_to_value(TransactionStatus.FINALIZADO), Transacao.valor_liquido_vendedor), else_=0)),
            # Valor em Custódia: ESCROW + ENVIADO
            func.sum(case((Transacao.status.in_([status_to_value(TransactionStatus.ESCROW), 
                                                status_to_value(TransactionStatus.ENVIADO)]),
                        Transacao.valor_liquido_vendedor), else_=0)),
            # A Liquidar: ENTREGUE
            func.sum(case((Transacao.status == status_to_value(TransactionStatus.ENTREGUE), Transacao.valor_liquido_vendedor), else_=0))
        ).filter(Transacao.vendedor_id == current_user.id).first()
        
        # 2. Últimas Vendas
        ultimas_vendas = Transacao.query.filter_by(vendedor_id=current_user.id)\
            .order_by(Transacao.data_criacao.desc())\
            .limit(5).all()
            
        vendas_data = []
        for t in ultimas_vendas:
            vendas_data.append({
                'id': t.id,
                'produto': t.safra.produto.nome if t.safra else 'Produto Indisponível',
                'valor': float(t.valor_liquido_vendedor or 0),
                'status': get_status_description(t.status),
                'data': t.data_criacao.isoformat(),
                'comprador': t.comprador.nome
            })
            
        return api_success({
            'kpis': {
                'receita_total': float(stats[0] or 0),
                'em_custodia': float(stats[1] or 0),
                'a_liquidar': float(stats[2] or 0),
                'saldo_disponivel': float(current_user.saldo_disponivel or 0)
            },
            'ultimas_vendas': vendas_data
        })
        
    except Exception as e:
        return api_error(str(e), 500)


# --- DASHBOARD ADMIN ---
@api_bp.route('/dashboard/admin', methods=['GET'])
@login_required
def dashboard_admin():
    """Dados para o dashboard do administrador."""
    if current_user.tipo != 'admin':
        return api_error('Acesso não autorizado', 403)
    
    try:
        # KPIs Globais
        total_users = Usuario.query.count()
        
        volume_vendas = db.session.query(func.sum(Transacao.valor_total_pago)).filter(
            Transacao.status == status_to_value(TransactionStatus.FINALIZADO)
        ).scalar() or 0
        
        comissoes = db.session.query(func.sum(Transacao.comissao_plataforma)).filter(
            Transacao.status == status_to_value(TransactionStatus.FINALIZADO)
        ).scalar() or 0
        
        transacoes_pendentes = Transacao.query.filter(
            Transacao.status.in_([
                status_to_value(TransactionStatus.PENDENTE),
                status_to_value(TransactionStatus.AGUARDANDO_PAGAMENTO),
                status_to_value(TransactionStatus.ANALISE)
            ])
        ).count()
        
        # Pagamentos para Validar
        pagamentos_validar = Transacao.query.filter(
            Transacao.status == status_to_value(TransactionStatus.ANALISE)
        ).count()
        
        # Liquidações Pendentes
        liquidacoes_pendentes = Transacao.query.filter(
            Transacao.status == status_to_value(TransactionStatus.ENTREGUE),
            Transacao.transferencia_concluida == False
        ).count()
        
        # Contas para Validar (NOVO)
        contas_validar = Usuario.query.filter_by(conta_validada=False, perfil_completo=True).count()
        
        return api_success({
            'kpis': {
                'total_users': total_users,
                'volume_vendas': float(volume_vendas),
                'comissoes': float(comissoes),
                'transacoes_pendentes': transacoes_pendentes
            },
            'tasks': {
                'pagamentos_validar': pagamentos_validar,
                'liquidacoes_pendentes': liquidacoes_pendentes,
                'contas_validar': contas_validar
            }
        })

    except Exception as e:
        return api_error(str(e), 500)


# --- GESTÃO DE UTILIZADORES (ADMIN) ---

@api_bp.route('/admin/usuarios/pendentes', methods=['GET'])
@login_required
def admin_usuarios_pendentes():
    """Lista utilizadores que completaram o perfil mas aguardam validação."""
    if current_user.tipo != 'admin':
        return api_error('Acesso restrito', 403)
        
    try:
        pendentes = Usuario.query.filter_by(
            conta_validada=False, 
            perfil_completo=True
        ).order_by(Usuario.data_cadastro.desc()).all()
        
        lista = [{
            'id': u.id,
            'nome': u.nome,
            'tipo': u.tipo,
            'telemovel': u.telemovel,
            'nif': u.nif,
            'foto': f"/uploads/perfil/{u.foto_perfil}" if u.foto_perfil else None,
            'data_cadastro': u.data_cadastro.isoformat()
        } for u in pendentes]
        
        return api_success(lista)
    except Exception as e:
        return api_error(str(e), 500)


@api_bp.route('/admin/usuarios/<int:id>/validar', methods=['POST'])
@login_required
def admin_validar_usuario(id):
    """Ativa a conta do utilizador."""
    if current_user.tipo != 'admin':
        return api_error('Acesso restrito', 403)
        
    try:
        usuario = Usuario.query.get_or_404(id)
        usuario.conta_validada = True
        
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="VALIDAR_CONTA",
            detalhes=f"User ID: {usuario.id} ({usuario.nome})",
            ip=request.remote_addr
        ))
        
        db.session.commit()
        return api_success({}, message=f"Conta de {usuario.nome} ativada com sucesso!")
        
    except Exception as e:
        db.session.rollback()
        return api_error(str(e), 500)


# --- TRANSAÇÕES (COMPRAR) ---
@api_bp.route('/comprar', methods=['POST'])
@login_required
def criar_pedido():
    """Cria uma reserva de compra (transação PENDENTE)."""
    if current_user.tipo != 'comprador':
        return api_error('Apenas compradores podem realizar encomendas', 403)
        
    try:
        data = request.get_json()
        if not data:
            return api_error('Dados inválidos', 400)
            
        safra_id = data.get('safra_id')
        quantidade = Decimal(str(data.get('quantidade', 0)))
        
        if quantidade <= 0:
            return api_error('Quantidade inválida', 400)
            
        # Lock da Safra (Para evitar condições de corrida)
        safra = Safra.query.with_for_update().get(safra_id)
        
        if not safra:
            return api_error('Safra não encontrada', 404)
            
        if safra.produtor_id == current_user.id:
            return api_error('Não pode comprar os seus próprios produtos', 400)
            
        if safra.status != 'disponivel' or safra.quantidade_disponivel < quantidade:
            return api_error('Stock insuficiente ou safra indisponível', 400)
            
        # Criar Transação
        valor_total = (safra.preco_por_unidade * quantidade)
        
        nova_transacao = Transacao(
            safra_id=safra.id,
            comprador_id=current_user.id,
            vendedor_id=safra.produtor_id,
            quantidade_comprada=quantidade,
            valor_total_pago=valor_total,
            status=status_to_value(TransactionStatus.PENDENTE)
        )
        
        # Abater Stock Temporariamente (Reserva)
        safra.quantidade_disponivel -= quantidade
        
        db.session.add(nova_transacao)
        db.session.flush() # Gera o ID e Fatura Ref
        
        # Notificar Produtor
        db.session.add(Notificacao(
            usuario_id=safra.produtor_id,
            mensagem=f"📦 Novo pedido de {quantidade}kg na safra de {safra.produto.nome}!",
            link=url_for('produtor.vendas') # ou endpoint da API
        ))
        
        # Log
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="CRIAR_PEDIDO",
            detalhes=f"Ref: {nova_transacao.fatura_ref} | Qtd: {quantidade}",
            ip=request.remote_addr
        ))
        
        db.session.commit()
        
        return api_success({
            'transacao_id': nova_transacao.id,
            'ref': nova_transacao.fatura_ref,
            'valor_total': float(valor_total)
        }, message='Pedido criado com sucesso!')
        
    except Exception as e:
        db.session.rollback()
        return api_error(f"Erro ao processar pedido: {str(e)}", 500)


# --- FLUXO DO PRODUTOR (PUBLICAR E GERIR) ---

@api_bp.route('/produtor/nova-safra', methods=['POST'])
@login_required
def api_nova_safra():
    """Endpoint para publicar uma nova safra via API (FormData)."""
    if current_user.tipo != 'produtor':
        return api_error('Apenas produtores podem publicar safras', 403)
        
    # ATENÇÃO: Se a conta não estiver validada, bloqueia.
    # Para testes, certifique-se que o user tem conta_validada=True na BD.
    if not current_user.conta_validada:
        return api_error('A tua conta precisa de ser validada pela administração', 403)

    try:
        # FormData
        produto_id = request.form.get('produto_id')
        qtd_str = request.form.get('quantidade_kg')
        preco_str = request.form.get('preco_kg')
        descricao = request.form.get('descricao', '')
        imagem_file = request.files.get('imagem_safra')

        if not produto_id or not qtd_str or not preco_str:
            return api_error('Campos obrigatórios em falta', 400)

        # Sanitização Numérica
        try:
            qtd = Decimal(qtd_str.replace(',', '.'))
            preco = Decimal(preco_str.replace(',', '.'))
        except InvalidOperation:
            return api_error('Quantidade ou preço inválidos', 400)

        if qtd <= 0 or preco <= 0:
            return api_error('Valores devem ser positivos', 400)

        # Upload de Imagem
        nome_foto = "default_safra.webp"
        if imagem_file:
            salvo = salvar_ficheiro(imagem_file, subpasta='safras')
            if salvo:
                nome_foto = salvo
            else:
                return api_error('Formato de imagem inválido', 400)

        nova_s = Safra(
            produtor_id=current_user.id,
            produto_id=int(produto_id),
            quantidade_disponivel=qtd,
            preco_por_unidade=preco,
            observacoes=descricao,
            imagem=nome_foto,
            status='disponivel'
        )
        
        db.session.add(nova_s)
        db.session.flush()

        # Log
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="SAFRA_CRIADA",
            detalhes=f"ID: {nova_s.id} | Produto: {nova_s.produto_id} | Qtd: {qtd}",
            ip=request.remote_addr
        ))

        db.session.commit()
        return api_success({'safra_id': nova_s.id}, message='Safra publicada com sucesso!')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO NOVA SAFRA: {e}")
        return api_error(f"Erro ao publicar safra: {str(e)}", 500)


@api_bp.route('/produtor/transacoes/<int:id>/status', methods=['POST'])
@login_required
def api_mudar_status_transacao(id):
    """
    Permite ao produtor:
    - ACEITAR (Pendente -> Aguardando Pagamento)
    - RECUSAR (Pendente -> Cancelado)
    - ENVIAR (Escrow -> Enviado)
    """
    if current_user.tipo != 'produtor':
        return api_error('Acesso restrito a produtores', 403)

    try:
        data = request.get_json()
        acao = data.get('acao') # 'aceitar', 'recusar', 'enviar'
        
        if not acao:
            return api_error('Ação não especificada', 400)

        # Lock para evitar conflitos
        transacao = Transacao.query.with_for_update().get(id)
        
        if not transacao:
            return api_error('Transação não encontrada', 404)
            
        if transacao.vendedor_id != current_user.id:
            return api_error('Esta transação não lhe pertence', 403)

        mensagem = ""
        
        if acao == 'aceitar':
            if transacao.status != status_to_value(TransactionStatus.PENDENTE):
                return api_error('Só pode aceitar reservas pendentes', 400)
                
            transacao.mudar_status(status_to_value(TransactionStatus.AGUARDANDO_PAGAMENTO), "Aceite pelo produtor")
            mensagem = "Pedido aceite! O comprador foi notificado para pagar."
            
            # Notificar Comprador
            db.session.add(Notificacao(
                usuario_id=transacao.comprador_id,
                mensagem=f"✅ O seu pedido {transacao.fatura_ref} foi aceite! Por favor, proceda ao pagamento.",
                link="/comprador/minhas-reservas"
            ))

        elif acao == 'recusar':
            if transacao.status != status_to_value(TransactionStatus.PENDENTE):
                return api_error('Só pode recusar reservas pendentes', 400)
            
            # Devolver stock
            if transacao.safra:
                transacao.safra.quantidade_disponivel += transacao.quantidade_comprada
                
            transacao.mudar_status(status_to_value(TransactionStatus.CANCELADO), "Recusada pelo produtor")
            mensagem = "Reserva recusada e stock reposto."
            
            # Notificar Comprador
            db.session.add(Notificacao(
                usuario_id=transacao.comprador_id,
                mensagem=f"❌ O pedido {transacao.fatura_ref} foi recusado pelo produtor.",
                link="/dashboard"
            ))

        elif acao == 'enviar':
            if transacao.status != status_to_value(TransactionStatus.ESCROW):
                return api_error('O pagamento deve ser confirmado antes do envio (Status: Escrow)', 400)
                
            transacao.mudar_status(status_to_value(TransactionStatus.ENVIADO), "Mercadoria enviada")
            transacao.data_envio = datetime.now(timezone.utc)
            if hasattr(transacao, 'calcular_janela_logistica'):
                transacao.calcular_janela_logistica()
                
            mensagem = f"Envio confirmado! Ref: {transacao.fatura_ref}"
            
            # Notificar Comprador
            db.session.add(Notificacao(
                usuario_id=transacao.comprador_id,
                mensagem=f"🚚 A sua encomenda {transacao.fatura_ref} foi enviada! Acompanhe a entrega.",
                link="/comprador/minhas-compras"
            ))

        else:
            return api_error('Ação inválida', 400)

        # Log
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao=f"TRANSACAO_{acao.upper()}",
            detalhes=f"Ref: {transacao.fatura_ref}",
            ip=request.remote_addr
        ))

        db.session.commit()
        return api_success({}, message=mensagem)

    except Exception as e:
        db.session.rollback()
        return api_error(f"Erro ao processar ação: {str(e)}", 500)


# --- FLUXO DO ADMIN (FINANCEIRO) ---

@api_bp.route('/admin/tarefas', methods=['GET'])
@login_required
def admin_tarefas():
    """Retorna listas de tarefas financeiras pendentes para o Admin."""
    if current_user.tipo != 'admin':
        return api_error('Acesso restrito', 403)

    try:
        # 1. Pagamentos para Validar (Comprovativos enviados)
        # Status: ANALISE
        validacoes = Transacao.query.filter_by(status=status_to_value(TransactionStatus.ANALISE)).all()
        lista_validacoes = [{
            'id': t.id,
            'ref': t.fatura_ref,
            'comprador': t.comprador.nome,
            'valor': float(t.valor_total_pago),
            'data': t.data_criacao.isoformat(),
            'comprovativo': f"/uploads/comprovativos/{t.comprovativo_path}" if t.comprovativo_path else None
        } for t in validacoes]

        # 2. Liquidações Pendentes (Entregas confirmadas, dinheiro por transferir ao produtor)
        # Status: ENTREGUE, e transferencia_concluida = False
        liquidacoes = Transacao.query.filter_by(
            status=status_to_value(TransactionStatus.ENTREGUE),
            transferencia_concluida=False
        ).all()
        
        lista_liquidacoes = [{
            'id': t.id,
            'ref': t.fatura_ref,
            'produtor': t.vendedor.nome,
            'iban': t.vendedor.iban,
            'valor_liquido': float(t.valor_liquido_vendedor), # Já descontada a comissão
            'comissao': float(t.comissao_plataforma),
            'data_entrega': t.data_entrega.isoformat() if t.data_entrega else None
        } for t in liquidacoes]
        
        # 3. Contas para Validar
        contas_validar = Usuario.query.filter_by(conta_validada=False, perfil_completo=True).count()

        return api_success({
            'validacoes': lista_validacoes,
            'liquidacoes': lista_liquidacoes,
            'contas_validar': contas_validar
        })

    except Exception as e:
        return api_error(str(e), 500)


@api_bp.route('/admin/transacoes/<int:id>/processar', methods=['POST'])
@login_required
def admin_processar_transacao(id):
    """
    Endpoint centralizado para decisões do Admin:
    - VALIDAR_PAGAMENTO (Analise -> Escrow)
    - REJEITAR_PAGAMENTO (Analise -> Aguardando Pagamento)
    - CONFIRMAR_TRANSFERENCIA (Entregue -> Finalizado)
    """
    if current_user.tipo != 'admin':
        return api_error('Acesso restrito', 403)

    try:
        data = request.get_json()
        acao = data.get('acao') # 'validar', 'rejeitar', 'liquidar'
        motivo = data.get('motivo', '') # Opcional, para rejeições

        transacao = Transacao.query.with_for_update().get_or_404(id)
        msg_sucesso = ""

        if acao == 'validar':
            if transacao.status != status_to_value(TransactionStatus.ANALISE):
                return api_error('Transação não está em análise', 400)
            
            transacao.mudar_status(status_to_value(TransactionStatus.ESCROW), "Pagamento validado pelo Admin")
            msg_sucesso = "Pagamento validado! O produtor pode enviar a mercadoria."
            
            # Notificar Produtor
            db.session.add(Notificacao(
                usuario_id=transacao.vendedor_id,
                mensagem=f"💰 Pagamento confirmado para a encomenda {transacao.fatura_ref}! Pode enviar a mercadoria.",
                link="/produtor/vendas"
            ))

        elif acao == 'rejeitar':
            # Se rejeitar, volta para AGUARDANDO_PAGAMENTO para o comprador tentar de novo
            transacao.mudar_status(status_to_value(TransactionStatus.AGUARDANDO_PAGAMENTO), f"Rejeitado: {motivo}")
            transacao.comprovativo_path = None # Limpa para novo upload
            msg_sucesso = "Comprovativo rejeitado. O comprador foi notificado."

            # Notificar Comprador
            db.session.add(Notificacao(
                usuario_id=transacao.comprador_id,
                mensagem=f"❌ O seu comprovativo para {transacao.fatura_ref} foi rejeitado. Motivo: {motivo}",
                link="/comprador/minhas-reservas"
            ))

        elif acao == 'liquidar':
            if transacao.status != status_to_value(TransactionStatus.ENTREGUE):
                return api_error('A encomenda deve estar entregue para ser liquidada', 400)
            
            transacao.transferencia_concluida = True
            transacao.mudar_status(status_to_value(TransactionStatus.FINALIZADO), "Liquidado ao produtor")
            transacao.data_liquidacao = datetime.now(timezone.utc)
            msg_sucesso = "Liquidação registada com sucesso! O ciclo fechou."

            # Notificar Produtor
            db.session.add(Notificacao(
                usuario_id=transacao.vendedor_id,
                mensagem=f"💵 Transferência realizada para a venda {transacao.fatura_ref}!",
                link="/produtor/dashboard"
            ))

        else:
            return api_error('Ação desconhecida', 400)

        # Log
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao=f"ADMIN_{acao.upper()}",
            detalhes=f"Ref: {transacao.fatura_ref} | Motivo: {motivo}",
            ip=request.remote_addr
        ))

        db.session.commit()
        return api_success({}, message=msg_sucesso)

    except Exception as e:
        db.session.rollback()
        return api_error(f"Erro no processamento: {str(e)}", 500)


# --- HEALTH CHECK DA API ---
@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check específico da API."""
    return api_success({
        'status': 'healthy',
        'version': '1.0.0',
        'service': 'AgroKongo API'
    })
