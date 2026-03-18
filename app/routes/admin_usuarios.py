"""
Blueprint para gestão de usuários do Admin.
Responsável por validação, visualização e eliminação de usuários.
"""
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, or_

from app.extensions import db
from app.models import Usuario, Transacao, LogAuditoria, TransactionStatus, Notificacao
from app.utils.status_helper import status_to_value
from functools import wraps
from decimal import Decimal

admin_usuarios_bp = Blueprint('admin_usuarios', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != 'admin':
            flash("Acesso restrito a administradores.", "danger")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_usuarios_bp.route('/usuarios')
@login_required
@admin_required
def lista_usuarios():
    usuarios = Usuario.query.filter(Usuario.tipo != 'admin').order_by(Usuario.nome).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)


@admin_usuarios_bp.route('/usuario/<int:user_id>')
@login_required
@admin_required
def detalhes_usuario(user_id):
    user = Usuario.query.get_or_404(user_id)

    stats = {
        'total_faturado': Decimal('0.00'),
        'em_custodia': Decimal('0.00'),
        'vendas_concluidas': 0,
        'total_gasto': Decimal('0.00')
    }

    if user.tipo == 'produtor':
        transacoes = Transacao.query.filter_by(vendedor_id=user.id).order_by(Transacao.data_criacao.desc()).all()

        stats['total_faturado'] = db.session.query(func.sum(Transacao.valor_liquido_vendedor)).filter(
            Transacao.vendedor_id == user.id,
            Transacao.transferencia_concluida == True
        ).scalar() or Decimal('0.00')

        stats['em_custodia'] = db.session.query(func.sum(Transacao.valor_liquido_vendedor)).filter(
            Transacao.vendedor_id == user.id,
            Transacao.status.in_([status_to_value(TransactionStatus.ESCROW), status_to_value(TransactionStatus.ENVIADO), status_to_value(TransactionStatus.ENTREGUE)]),
            Transacao.transferencia_concluida == False
        ).scalar() or Decimal('0.00')

        stats['vendas_concluidas'] = Transacao.query.filter_by(vendedor_id=user.id,
                                                               transferencia_concluida=True).count()
    else:
        transacoes = Transacao.query.filter_by(comprador_id=user.id).order_by(Transacao.data_criacao.desc()).all()
        stats['total_gasto'] = db.session.query(func.sum(Transacao.valor_total_pago)).filter_by(
            comprador_id=user.id).scalar() or Decimal('0.00')

    logs_relacionados = LogAuditoria.query.filter(
        or_(
            LogAuditoria.usuario_id == user.id,
            LogAuditoria.detalhes.contains(user.nome),
            LogAuditoria.detalhes.contains(user.nif if user.nif else "NIF_NAO_DISPONIVEL")
        )
    ).order_by(LogAuditoria.data_criacao.desc()).limit(50).all()

    return render_template('admin/detalhes_usuario.html',
                           user=user,
                           transacoes=transacoes,
                           logs=logs_relacionados,
                           stats=stats)


@admin_usuarios_bp.route('/validar-usuario/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def validar_usuario(user_id):
    try:
        user = Usuario.query.get_or_404(user_id)
        user.conta_validada = True

        nova_notificacao = Notificacao(
            usuario_id=user.id,
            mensagem="Sua conta foi validada com sucesso! Já pode operar no mercado."
        )
        db.session.add(nova_notificacao)

        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="Validação de Conta",
            detalhes=f"Validou o perfil de {user.nome}",
            ip=request.remote_addr
        ))

        db.session.commit()
        flash(f'Utilizador {user.nome} validado com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro validar user: {e}")
        flash("Erro ao validar utilizador.", "danger")
        
    return redirect(url_for('admin_usuarios.lista_usuarios'))


@admin_usuarios_bp.route('/rejeitar-usuario/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def rejeitar_usuario(user_id):
    try:
        user = Usuario.query.get_or_404(user_id)
        motivo = request.form.get('motivo_rejeicao', 'Documentação inconsistente.')

        user.perfil_completo = False
        user.conta_validada = False

        notif = Notificacao(
            usuario_id=user.id,
            mensagem=f"⚠️ Seu perfil foi rejeitado. Motivo: {motivo}"
        )

        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="Rejeição de Perfil",
            detalhes=f"Rejeitou o perfil de {user.nome}. Motivo: {motivo}",
            ip=request.remote_addr
        ))

        db.session.add(notif)
        db.session.commit()

        flash(f'O utilizador {user.nome} foi notificado.', 'info')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro rejeitar user: {e}")
        flash("Erro ao rejeitar utilizador.", "danger")
        
    return redirect(url_for('admin_usuarios.detalhes_usuario', user_id=user.id))


@admin_usuarios_bp.route('/usuario/eliminar/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def eliminar_usuario(user_id):
    try:
        usuario = Usuario.query.get_or_404(user_id)

        # Limpeza de Ficheiros Físicos
        if usuario.foto_perfil:
            caminho_foto = os.path.join(current_app.config['UPLOAD_FOLDER_PUBLIC'], 'perfil', usuario.foto_perfil)
            if os.path.exists(caminho_foto):
                try: 
                    os.remove(caminho_foto)
                except: 
                    pass

        if usuario.documento_pdf:
            caminho_pdf = os.path.join(current_app.config['UPLOAD_FOLDER_PRIVATE'], 'documentos', usuario.documento_pdf)
            if os.path.exists(caminho_pdf):
                try: 
                    os.remove(caminho_pdf)
                except: 
                    pass

        db.session.delete(usuario)
        
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="DELETE_USER",
            detalhes=f"Eliminou user {usuario.nome} (ID: {user_id})",
            ip=request.remote_addr
        ))
        
        db.session.commit()

        flash(f'O utilizador {usuario.nome} foi eliminado com sucesso.', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao eliminar user: {e}")
        flash(f'Erro ao eliminar utilizador: {str(e)}', 'danger')

    return redirect(url_for('admin_usuarios.lista_usuarios'))
