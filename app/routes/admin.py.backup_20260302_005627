import os
import pandas as pd
from io import BytesIO
from decimal import Decimal
from datetime import timedelta, datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, \
    send_from_directory, abort
from flask_login import login_required, current_user
from sqlalchemy import func, or_, case

from app import scheduler
from app.models import (
    Usuario, Transacao, Notificacao, LogAuditoria,
    Safra, Produto, TransactionStatus
)
from app.extensions import db
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__)


# --- DASHBOARD DE CONTROLO ---
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Painel de Gestão Centralizada e KPIs Financeiros."""
    # 1. Agregações SQL de Alta Performance
    financas = db.session.query(
        func.sum(case((Transacao.status != TransactionStatus.CANCELADO, Transacao.valor_total_pago), else_=0)),
        func.sum(case((Transacao.status == TransactionStatus.FINALIZADO, Transacao.comissao_plataforma), else_=0)),
        func.sum(case((Transacao.status == TransactionStatus.ENTREGUE, Transacao.valor_liquido_vendedor), else_=0))
    ).first()

    # 2. Filas de Trabalho Prioritárias
    # Talões que precisam de conferência IMEDIATA para não travar o produtor
    pendentes_validacao = Transacao.query.filter_by(status=TransactionStatus.ANALISE) \
        .order_by(Transacao.data_criacao.asc()).all()

    # Dinheiro que já pode ser enviado aos produtores (Mercadoria entregue)
    aguardando_liquidacao = Transacao.query.filter_by(
        status=TransactionStatus.ENTREGUE,
        transferencia_concluida=False
    ).all()

    # 3. Stock Estratégico
    stock_global = db.session.query(Produto.nome, func.sum(Safra.quantidade_disponivel)) \
        .join(Safra).filter(Safra.status == 'disponivel') \
        .group_by(Produto.nome).all()

    return render_template('admin/dashboard.html',
                           total_vendas=financas[0] or 0,
                           comissao_total=financas[1] or 0,
                           divida_produtores=financas[2] or 0,
                           pendentes=pendentes_validacao,
                           dividas=aguardando_liquidacao,
                           safras_ativas=stock_global,
                           total_utilizadores=Usuario.query.count())


# --- MOTOR DE ESCROW (PAGAMENTOS) ---
@admin_bp.route('/validar-pagamento/<int:id>', methods=['POST'])
@login_required
@admin_required
def validar_pagamento(id):
    # 1. Busca a venda com bloqueio de linha (Pessimistic Locking)
    # Importante: O with_for_update deve estar dentro de um bloco de transação
    venda = Transacao.query.with_for_update().get_or_404(id)

    if venda.status != TransactionStatus.ANALISE:
        flash('Esta transação já foi processada ou não está em análise.', 'warning')
        return redirect(url_for('admin.dashboard'))

    try:
        # 2. Atualização do Status
        venda.status = TransactionStatus.ESCROW

        # 3. Registo de Auditoria
        log = LogAuditoria(
            usuario_id=current_user.id,
            acao="VALIDACAO_PAGAMENTO",
            detalhes=f"Ref {venda.fatura_ref} aprovada e movida para ESCROW."
        )
        db.session.add(log)

        # 4. Commit primeiro para garantir que os dados estão salvos antes da tarefa começar
        db.session.commit()

        # 5. DISPARO ASSÍNCRONO VIA APSCHEDULER (Em vez de Celery .delay)
        # Importamos a função aqui para evitar importação circular
        from app.tasks import enviar_fatura_email

        # Adicionamos um job que corre "agora" (uma única vez)
        scheduler.add_job(
            id=f'envio_fatura_{venda.id}',
            func=enviar_fatura_email,
            args=[venda.id],
            trigger='date',  # Executa uma vez numa data específica
            run_date=None  # None significa "executar imediatamente"
        )

        flash(f'Pagamento {venda.fatura_ref} validado! A fatura está a ser processada em segundo plano.', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO_ADMIN_VALIDACAO (ID: {id}): {e}")
        flash('Erro técnico ao processar a validação.', 'danger')

    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/confirmar-transferencia/<int:id>', methods=['POST'])
@login_required
@admin_required
def confirmar_transferencia(id):
    """O Admin confirma que já fez a transferência bancária para o IBAN do produtor."""
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    # Proteção CSRF
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
    venda = Transacao.query.with_for_update().get_or_404(id)

    if venda.status == TransactionStatus.ENTREGUE and venda.transferencia_concluida is False:
        try:
            venda.transferencia_concluida = True
            venda.status = TransactionStatus.FINALIZADO
            venda.data_liquidacao = datetime.now(timezone.utc)

            # Notifica o Produtor sobre o dinheiro na conta
            db.session.add(Notificacao(
                usuario_id=venda.vendedor_id,
                mensagem=f"💵 Pagamento enviado para o seu IBAN (Ref: {venda.fatura_ref}).",
                link=url_for('produtor.dashboard')
            ))

            db.session.commit()
            flash("Liquidação concluída com sucesso!", "success")
        except Exception:
            db.session.rollback()
            flash("Erro ao processar liquidação.", "danger")

    return redirect(url_for('admin.dashboard'))


# --- GESTÃO DE DISPUTAS ---
@admin_bp.route('/resolver-disputa/<int:trans_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def resolver_disputa(trans_id):
    """Juiz do Mercado: Decide se devolve o dinheiro ao comprador ou paga ao produtor."""
    venda = Transacao.query.get_or_404(trans_id)

    if request.method == 'POST':
        from flask_wtf.csrf import validate_csrf
        from wtforms import ValidationError
        
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            abort(403)
        
        decisao = request.form.get('decisao')  # 'libertar' ou 'reembolsar'

        if decisao == 'libertar':
            venda.status = TransactionStatus.ENTREGUE
            msg = "Disputa resolvida a favor do Produtor."
        else:
            venda.status = TransactionStatus.CANCELADO
            venda.safra.quantidade_disponivel += venda.quantidade_comprada
            msg = "Disputa resolvida com Reembolso ao Comprador."

        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="RESOLUCAO_DISPUTA",
            detalhes=f"Ref {venda.fatura_ref}: {msg}"
        ))
        db.session.commit()
        flash("Disputa encerrada.", "success")
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/detalhe_disputa.html', venda=venda)


# --- RELATÓRIOS E EXPORTAÇÃO ---
@admin_bp.route('/exportar-financeiro-agro')
@login_required
@admin_required
def exportar_financeiro():
    """Gera um relatório financeiro de nível executivo para instituições."""
    vendas = Transacao.query.all()
    dados_vendas = _preparar_dados_vendas(vendas)
    output = _gerar_excel_financeiro(dados_vendas)
    
    return send_file(output, as_attachment=True,
                     download_name=f"AGROKONGO_FINANCEIRO_{datetime.now().strftime('%d_%m_%Y')}.xlsx")


def _preparar_dados_vendas(vendas):
    """Prepara dados das vendas para exportação."""
    dados_vendas = []
    for v in vendas:
        bruto = float(v.valor_total_pago)
        comissao = float(v.comissao_plataforma or 0)
        liquido = bruto - comissao

        dados_vendas.append({
            'ID OPERAÇÃO': f"AGK-{v.id:06d}",
            'DATA VALOR': v.data_criacao.strftime('%d/%m/%Y'),
            'REF. FATURA': v.fatura_ref or "S/REF",
            'PRODUTOR': v.vendedor.nome.upper(),
            'NIF PRODUTOR': getattr(v.vendedor, 'nif', 'CONSULTAR'),
            'IBAN DE DESTINO': v.vendedor.iban or 'PENDENTE',
            'VALOR BRUTO (Kz)': bruto,
            'TAXA SERVIÇO (Kz)': comissao,
            'VALOR LÍQUIDO (Kz)': liquido,
            'STATUS PAGAMENTO': v.status.replace('_', ' ').upper()
        })
    return dados_vendas


def _criar_formatos_excel(workbook):
    """Cria formatos de estilo para o Excel."""
    return {
        'header': workbook.add_format({
            'bold': True, 'bg_color': '#1B4332', 'font_color': 'white',
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 11
        }),
        'money': workbook.add_format({'num_format': '#,##0.00" Kz"', 'border': 1, 'font_size': 10}),
        'date': workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1, 'align': 'center'}),
        'text': workbook.add_format({'border': 1, 'font_size': 10}),
        'title': workbook.add_format({'bold': True, 'font_size': 18, 'font_color': '#1B4332'}),
        'label': workbook.add_format({'bold': True, 'bg_color': '#F8F9FA', 'border': 1})
    }


def _escrever_cabecalho_excel(worksheet, formatos):
    """Escreve cabeçalho corporativo no Excel."""
    worksheet.write('A1', 'AGROKONGO - RELATÓRIO DE CONCILIAÇÃO FINANCEIRA', formatos['title'])
    worksheet.write('A2', f'Período: Até {datetime.now().strftime("%d/%m/%Y")}')
    worksheet.write('A3', 'Finalidade: Instrução de Transferência / Auditoria AGT')


def _escrever_sumario_excel(worksheet, formatos, total_linhas):
    """Escreve sumário de totais no Excel."""
    worksheet.write('F3', 'TOTAL EM CUSTÓDIA', formatos['label'])
    worksheet.write_formula('G3', f'=SUM(G6:G{total_linhas + 6})', formatos['money'])
    worksheet.write('H3', 'LÍQUIDO A PAGAR', formatos['label'])
    worksheet.write_formula('I3', f'=SUM(I6:I{total_linhas + 6})', formatos['money'])


def _formatar_colunas_excel(worksheet, df, formatos):
    """Formata colunas e cabeçalhos da tabela."""
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(5, col_num, value, formatos['header'])
    
    worksheet.set_column('A:A', 14, formatos['text'])
    worksheet.set_column('B:B', 14, formatos['date'])
    worksheet.set_column('C:C', 16, formatos['text'])
    worksheet.set_column('D:D', 30, formatos['text'])
    worksheet.set_column('E:E', 15, formatos['text'])
    worksheet.set_column('F:F', 28, formatos['text'])
    worksheet.set_column('G:I', 20, formatos['money'])
    worksheet.set_column('J:J', 20, formatos['text'])


def _aplicar_formatacao_condicional(worksheet, workbook, total_linhas):
    """Aplica formatação condicional ao Excel."""
    worksheet.conditional_format(6, 9, total_linhas + 6, 9, {
        'type': 'cell', 'criteria': 'containing', 'value': 'PAGO',
        'format': workbook.add_format({'bg_color': '#DFF0D8', 'font_color': '#3C763D'})
    })


def _gerar_excel_financeiro(dados_vendas):
    """Gera arquivo Excel completo com formatação."""
    df = pd.DataFrame(dados_vendas)
    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dashboard_Financeiro', startrow=5)
        workbook = writer.book
        worksheet = writer.sheets['Dashboard_Financeiro']
        
        formatos = _criar_formatos_excel(workbook)
        _escrever_cabecalho_excel(worksheet, formatos)
        _escrever_sumario_excel(worksheet, formatos, len(dados_vendas))
        _formatar_colunas_excel(worksheet, df, formatos)
        _aplicar_formatacao_condicional(worksheet, workbook, len(dados_vendas))

    output.seek(0)
    return output


# --- UTILITÁRIOS DE SERVIDOR ---
@admin_bp.route('/ver-comprovativo/<path:filename>')
@login_required
@admin_required
def ver_comprovativo(filename):
    """Acesso seguro a ficheiros privados (Talões)."""
    safe_filename = os.path.basename(filename)
    folder = os.path.join(current_app.config['UPLOAD_FOLDER_PRIVATE'], 'comprovativos')
    filepath = os.path.abspath(os.path.join(folder, safe_filename))
    folder_abs = os.path.abspath(folder)
    
    if not filepath.startswith(folder_abs + os.sep):
        abort(403)
    if not os.path.exists(filepath):
        abort(404)
    
    return send_from_directory(folder, safe_filename)


@admin_bp.route('/analisar-pagamento/<int:id>', methods=['GET'])
@login_required
@admin_required
def analisar_pagamento(id):
    venda = Transacao.query.get_or_404(id)

    # CONVERSÃO: Multiplicar Decimal por Decimal
    comissao = venda.valor_total_pago * Decimal('0.05')
    valor_produtor = venda.valor_total_pago - comissao

    return render_template('admin/analisar.html',
                           venda=venda,
                           comissao=comissao,
                           valor_produtor=valor_produtor)

# --- VALIDAÇÃO DE UTILIZADOR (CORRIGIDO) ---
@admin_bp.route('/validar-usuario/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def validar_usuario(user_id):
    user = Usuario.query.get_or_404(user_id)
    user.conta_validada = True

    # REMOVIDO: 'tipo="sucesso"' para evitar o TypeError
    nova_notificacao = Notificacao(
        usuario_id=user.id,
        mensagem="Sua conta foi validada com sucesso! Já pode operar no mercado."
    )
    db.session.add(nova_notificacao)

    db.session.add(LogAuditoria(
        usuario_id=current_user.id,
        acao="Validação de Conta",
        detalhes=f"Validou o perfil de {user.nome}")
    )

    db.session.commit()
    flash(f'Utilizador {user.nome} validado com sucesso!', 'success')
    # Certifique-se que o endpoint abaixo existe ou use 'admin.usuarios'
    return redirect(url_for('admin.lista_usuarios'))


# --- REJEIÇÃO DE UTILIZADOR (CORRIGIDO) ---
@admin_bp.route('/rejeitar-usuario/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def rejeitar_usuario(user_id):
    user = Usuario.query.get_or_404(user_id)
    motivo = request.form.get('motivo_rejeicao', 'Documentação inconsistente.')

    user.perfil_completo = False
    user.conta_validada = False

    # REMOVIDO: 'tipo="danger"' para evitar o TypeError
    notif = Notificacao(
        usuario_id=user.id,
        mensagem=f"⚠️ Seu perfil foi rejeitado. Motivo: {motivo}"
    )

    db.session.add(LogAuditoria(
        usuario_id=current_user.id,
        acao="Rejeição de Perfil",
        detalhes=f"Rejeitou o perfil de {user.nome}. Motivo: {motivo}"
    ))

    db.session.add(notif)
    db.session.commit()

    flash(f'O utilizador {user.nome} foi notificado.', 'info')
    return redirect(url_for('admin.detalhes_usuario', user_id=user.id))


# --- LISTA DE UTILIZADORES ---
@admin_bp.route('/usuarios')
@login_required
@admin_required
def lista_usuarios():
    usuarios = Usuario.query.filter(Usuario.tipo != 'admin').order_by(Usuario.nome).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)


# --- PAGAMENTOS PENDENTES AO PRODUTOR (CORRIGIDO) ---
@admin_bp.route('/pagamentos-pendentes')
@login_required
@admin_required
def pagamentos_pendentes():
    # Usar o Enum para garantir que o filtro funciona sempre
    vendas_a_pagar = Transacao.query.filter_by(
        status=TransactionStatus.ENTREGUE,
        transferencia_concluida=False
    ).all()
    return render_template('admin/pagamentos.html', vendas=vendas_a_pagar)


@admin_bp.route('/disputas')
@login_required
@admin_required
def painel_disputas():
    # Filtra apenas transações marcadas como 'em_disputa'
    disputas = Transacao.query.filter_by(status='em_disputa').order_by(Transacao.data_criacao.asc()).all()
    return render_template('admin/painel_disputas.html', disputas=disputas)


# --- LOGS ---
@admin_bp.route('/logs')
@login_required
@admin_required
def logs():
    lista_logs = LogAuditoria.query.order_by(LogAuditoria.data_criacao.desc()).limit(100).all()
    return render_template('admin/logs.html', logs=lista_logs)


@admin_bp.route('/usuario/<int:user_id>')
@login_required
@admin_required
def detalhes_usuario(user_id):
    user = Usuario.query.get_or_404(user_id)

    # 1. MÉTRICAS FINANCEIRAS (Para Produtores)
    stats = {
        'total_faturado': Decimal('0.00'),
        'em_custodia': Decimal('0.00'),
        'vendas_concluidas': 0
    }

    if user.tipo == 'produtor':
        # Histórico de Vendas
        transacoes = Transacao.query.filter_by(vendedor_id=user.id).order_by(Transacao.data_criacao.desc()).all()

        # Soma do que já foi efetivamente pago (Status FINALIZADO/CONCLUIDO)
        stats['total_faturado'] = db.session.query(func.sum(Transacao.valor_liquido_vendedor)).filter(
            Transacao.vendedor_id == user.id,
            Transacao.transferencia_concluida is True
        ).scalar() or Decimal('0.00')

        # Soma do que está "preso" aguardando liquidação (Status ESCROW/ENTREGUE)
        stats['em_custodia'] = db.session.query(func.sum(Transacao.valor_liquido_vendedor)).filter(
            Transacao.vendedor_id == user.id,
            Transacao.status.in_(['pago_escrow', 'mercadoria_enviada', 'entregue']),
            Transacao.transferencia_concluida is False
        ).scalar() or Decimal('0.00')

        stats['vendas_concluidas'] = Transacao.query.filter_by(vendedor_id=user.id,
                                                               transferencia_concluida=True).count()

    else:
        # Histórico de Compras para Compradores
        transacoes = Transacao.query.filter_by(comprador_id=user.id).order_by(Transacao.data_criacao.desc()).all()
        stats['total_gasto'] = db.session.query(func.sum(Transacao.valor_total_pago)).filter_by(
            comprador_id=user.id).scalar() or Decimal('0.00')

    # 2. LOGS DE AUDITORIA (Busca inteligente por Nome, NIF ou ID direto)
    # Melhorei o filtro para garantir que nada escapa ao rasto digital
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


@admin_bp.route('/rejeitar-pagamento/<int:id>', methods=['POST'])
@login_required
@admin_required
def rejeitar_pagamento(id):
    venda = Transacao.query.get_or_404(id)
    motivo = request.form.get('motivo', 'Não especificado')

    # REGISTO DE LOG
    db.session.add(LogAuditoria(
        usuario_id=current_user.id,
        acao="Rejeição de Pagamento",
        detalhes=f"Rejeitou pagamento da Ref: {venda.fatura_ref}. Motivo: {motivo}"
    ))

    venda.status = 'pendente'
    venda.comprovativo_path = None

    db.session.add(Notificacao(
        usuario_id=venda.comprador_id,
        mensagem=f"❌ Pagamento Rejeitado ({venda.fatura_ref}). Motivo: {motivo}. Envie novamente.",
        link=url_for('comprador.dashboard')
    ))

    db.session.commit()
    flash('Pagamento rejeitado e log registado.', 'info')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/historico-financeiro')
@login_required
@admin_required
def historico_financeiro():
    # 1. Talões validados (Ordenados pela data de criação, já que não temos data_validacao_específica)
    taloes_validados = Transacao.query.filter(
        Transacao.status.in_(['pago_escrow', 'mercadoria_enviada', 'mercadoria_entregue', 'finalizada_paga'])
    ).order_by(Transacao.data_criacao.desc()).all()

    # 2. Transferências feitas para produtores (Usando o campo data_transferencia que existe no seu Model)
    liquidacoes_concluidas = Transacao.query.filter(
        Transacao.transferencia_concluida is True
    ).order_by(Transacao.data_criacao.desc()).all()

    return render_template('admin/historico_financeiro.html',
                           taloes=taloes_validados,
                           liquidacoes=liquidacoes_concluidas)

@admin_bp.route('/detalhe-transacao/<int:id>')
@login_required
@admin_required
def detalhe_transacao(id):
    transacao = Transacao.query.get_or_404(id)
    return render_template('admin/detalhe_transacao.html', t=transacao)

# --- GERIR TALÕES (CORRIGIDO) ---
@admin_bp.route('/gerir-taloes')
@login_required
@admin_required
def gerir_taloes():
    # Filtros usando estritamente os Enums
    pendentes = Transacao.query.filter_by(status=TransactionStatus.ANALISE).all()

    validados = Transacao.query.filter(
        Transacao.status.in_([
            TransactionStatus.ESCROW,
            TransactionStatus.ENVIADO,
            TransactionStatus.ENTREGUE,
            TransactionStatus.FINALIZADO
        ])
    ).order_by(Transacao.data_criacao.desc()).all()

    return render_template('admin/gerir_taloes.html', pendentes=pendentes, validados=validados)


@admin_bp.route('/liquidar-pagamento/<int:trans_id>', methods=['POST'])
@login_required
@admin_required
def liquidar_pagamento(trans_id):
    venda = Transacao.query.get_or_404(trans_id)

    # Bloqueio preventivo: Se não estiver entregue, não processa o dinheiro
    if venda.status != TransactionStatus.ENTREGUE:
        flash('Bloqueio de Segurança: O comprador ainda não confirmou o recebimento desta mercadoria.', 'danger')
        return redirect(url_for('admin.dashboard'))

    # Se estiver tudo certo, procede com o pagamento
    venda.transferencia_concluida = True
    venda.status = TransactionStatus.FINALIZADO
    db.session.commit()

    flash('Repasse concluído com sucesso!', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/painel-pagamentos')
@login_required
@admin_required
def painel_pagamentos():
    # Buscamos apenas o que está 'ENTREGUE' mas ainda não foi transferido
    pendentes_liquidacao = Transacao.query.filter(
        Transacao.status == TransactionStatus.ENTREGUE,
        Transacao.transferencia_concluida is False
    ).all()

    return render_template('admin/painel_pagamentos.html', pendentes=pendentes_liquidacao)


@admin_bp.route('/tesouraria')
@login_required
@admin_required
def painel_liquidacoes():
    # Apenas o que o comprador já recebeu, mas o produtor ainda não recebeu o dinheiro
    vendas_pendentes = Transacao.query.filter(
        Transacao.status == TransactionStatus.ENTREGUE,
        Transacao.transferencia_concluida is False
    ).all()

    return render_template('admin/pagamentos.html', vendas=vendas_pendentes)


@admin_bp.route('/usuario/eliminar/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def eliminar_usuario(user_id):
    usuario = Usuario.query.get_or_404(user_id)

    try:
        # 1. Limpeza de Ficheiros Físicos com proteção contra path traversal
        if usuario.foto_perfil:
            safe_filename = os.path.basename(usuario.foto_perfil)
            folder_public = os.path.abspath(os.path.join(current_app.config['UPLOAD_FOLDER_PUBLIC'], 'perfil'))
            caminho_foto = os.path.abspath(os.path.join(folder_public, safe_filename))
            
            if caminho_foto.startswith(folder_public + os.sep) and os.path.exists(caminho_foto):
                os.remove(caminho_foto)

        if usuario.documento_pdf:
            safe_filename = os.path.basename(usuario.documento_pdf)
            folder_private = os.path.abspath(os.path.join(current_app.config['UPLOAD_FOLDER_PRIVATE'], 'documentos'))
            caminho_pdf = os.path.abspath(os.path.join(folder_private, safe_filename))
            
            if caminho_pdf.startswith(folder_private + os.sep) and os.path.exists(caminho_pdf):
                os.remove(caminho_pdf)

        # 2. Eliminar da Base de Dados
        db.session.delete(usuario)
        db.session.commit()

        flash(f'O utilizador {usuario.nome} foi eliminado com sucesso.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao eliminar utilizador: {str(e)}', 'danger')
        current_app.logger.error(f"Erro ao eliminar usuario {user_id}: {e}")

    return redirect(url_for('admin.lista_usuarios'))