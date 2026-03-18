from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Mensagem, Transacao, Notificacao

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/inbox')
@login_required
def inbox():
    """Lista todas as conversas ativas do utilizador."""
    # Busca transações onde o utilizador é comprador ou vendedor
    vendas_ativas = Transacao.query.filter(
        (Transacao.comprador_id == current_user.id) |
        (Transacao.vendedor_id == current_user.id)
    ).order_by(Transacao.data_criacao.desc()).all()

    return render_template('chat/inbox.html', vendas=vendas_ativas)


@chat_bp.route('/transacao/<int:trans_id>')
@login_required
def abrir_chat(trans_id):
    """Abre a conversa de uma transação específica com proteção de acesso."""
    venda = Transacao.query.get_or_404(trans_id)

    # Bloqueio de Intrusos
    if current_user.id not in [venda.comprador_id, venda.vendedor_id]:
        abort(403)

    mensagens = Mensagem.query.filter_by(transacao_id=trans_id) \
        .order_by(Mensagem.data_criacao.asc()).all()

    return render_template('chat/conversa.html', venda=venda, mensagens=mensagens)


@chat_bp.route('/enviar/<int:trans_id>', methods=['POST'])
@login_required
def enviar_mensagem(trans_id):
    """Envia mensagem com validação rigorosa de remetente."""
    venda = Transacao.query.get_or_404(trans_id)

    # SEGURANÇA: Só quem pertence à venda pode enviar mensagens
    if current_user.id not in [venda.comprador_id, venda.vendedor_id]:
        abort(403)

    conteudo = request.form.get('mensagem', '').strip()

    if not conteudo:
        return redirect(url_for('chat.abrir_chat', trans_id=trans_id))

    # 1. Gravação da Mensagem
    nova_msg = Mensagem(
        transacao_id=trans_id,
        remetente_id=current_user.id,
        conteudo=conteudo
    )
    db.session.add(nova_msg)

    # 2. Lógica de Notificação Inteligente
    destinatario_id = venda.vendedor_id if current_user.id == venda.comprador_id else venda.comprador_id

    # Verifica se já existe uma notificação não lida deste chat para evitar SPAM
    notif_existente = Notificacao.query.filter_by(
        usuario_id=destinatario_id,
        link=url_for('chat.abrir_chat', trans_id=trans_id),
        lida=False
    ).first()

    if not notif_existente:
        notif = Notificacao(
            usuario_id=destinatario_id,
            mensagem=f"💬 Nova mensagem de {current_user.nome} sobre a Ref {venda.fatura_ref}",
            link=url_for('chat.abrir_chat', trans_id=trans_id)
        )
        db.session.add(notif)

    db.session.commit()
    return redirect(url_for('chat.abrir_chat', trans_id=trans_id))