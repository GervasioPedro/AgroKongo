# app/socket_events.py - Eventos SocketIO realtime seguros e escaláveis (stock + futuro chat)
# Versão Corrigida - 22/02/2026
from flask_socketio import join_room, leave_room, emit, disconnect
from flask import request  # ← Import adicionado
from flask_login import current_user
from app.extensions import socketio, db, current_app
from app.models import Safra, TransactionStatus  # ← TransactionStatus adicionado
import logging

logger = logging.getLogger(__name__)  # ← Corrigido de 'name' para '__name__'


# ==================== CONEXÃO ====================
@socketio.on('connect')
def handle_connect(auth):
    """Autenticação obrigatória connect (token ou session)."""
    if not current_user.is_authenticated:
        logger.warning(f"Conexão SocketIO rejeitada: não autenticado (SID: {request.sid})")
        disconnect()
        return False

    logger.info(f"Cliente autenticado conectado: {current_user.id} (SID: {request.sid})")
    emit('connect_success', {'message': 'Conectado realtime!'})  # ← Corrigido espaço
    return True


@socketio.on('disconnect')
def handle_disconnect():
    """Log de desconexão (SocketIO limpa rooms automaticamente)."""
    logger.info(
        f"Cliente desconectado: {current_user.id if current_user.is_authenticated else 'Anônimo'} (SID: {request.sid})")
    # SocketIO limpa rooms auto


# ==================== ROOMS DE SAFRA ====================
@socketio.on('join_safra')
def on_join_safra(data):
    """Join room safra + emit stock inicial (UX live imediato)."""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Autenticação requerida.'})
        return

    safra_id = data.get('safra_id')
    if not safra_id:
        emit('error', {'message': 'safra_id obrigatório.'})
        return

    # ← Corrigido de 'ativo=True' para 'is_active=True' (consistência com models.py)
    safra = Safra.query.filter_by(id=safra_id, is_active=True, status='disponivel').first()

    if not safra:
        emit('error', {'message': 'Safra indisponível ou inexistente.'})
        return

    room = f"safra_{safra_id}"
    join_room(room)
    logger.info(f"Usuário {current_user.id} entrou room {room}")

    # Emit stock inicial (UX: tela atualiza imediato)
    emit('stock_update', {
        'safra_id': safra_id,
        'quantidade_disponivel': float(safra.quantidade_disponivel),
        'preco_por_unidade': float(safra.preco_por_unidade)
    })

    emit('join_success', {'message': f"Conectado realtime safra {safra_id}"})


@socketio.on('leave_safra')
def on_leave_safra(data):
    """Leave room safra (cleanup)."""
    safra_id = data.get('safra_id')
    if safra_id:
        room = f"safra_{safra_id}"
        leave_room(room)
        logger.info(f"Usuário {current_user.id if current_user.is_authenticated else 'Anônimo'} saiu room {room}")


# ==================== FUNÇÃO DE EMIT (USADA EM ROUTES) ====================
def emitir_atualizacao_stock(safra_id: int, novo_stock: float, preco: float = None):
    """
    Broadcast stock update room safra.
    Chamada de routes autenticadas (ex: reserva, cancelar).
    """
    room = f"safra_{safra_id}"
    payload = {
        'safra_id': safra_id,
        'quantidade_disponivel': float(novo_stock)
    }

    if preco is not None:
        payload['preco_por_unidade'] = float(preco)

    socketio.emit('stock_update', payload, room=room)
    logger.info(f"Stock update emitido room {room}: {novo_stock}")


# ==================== EVENTO DE RESERVA (OPCIONAL) ====================
@socketio.on('reservar_safra')
def on_reservar_safra(data):
    """
    Evento opcional para reserva via WebSocket (futuro).
    Atualmente reservas são via HTTP POST (mais seguro para transações financeiras).
    """
    if not current_user.is_authenticated:
        emit('error', {'message': 'Autenticação requerida.'})
        return

    safra_id = data.get('safra_id')
    quantidade = data.get('quantidade')

    if not safra_id or not quantidade:
        emit('error', {'message': 'Dados inválidos.'})
        return

    # Redireciona para HTTP (mais seguro para transações)
    emit('redirect_http', {
        'url': f'/reservar/{safra_id}',
        'message': 'Reservas devem ser confirmadas via HTTP para segurança.'
    })