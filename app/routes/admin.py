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
    Safra, Produto, TransactionStatus, db
)
from app.utils.status_helper import status_to_value
from functools import wraps

admin_bp = Blueprint('admin', __name__)

# --- DECORATOR DE SEGURANÇA ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != 'admin':
            flash("Acesso restrito a administradores.", "danger")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


# --- MOTOR DE ESCROW (PAGAMENTOS) ---
@admin_bp.route('/validar-pagamento/<int:id>', methods=['POST'])
@login_required
@admin_required
def validar_pagamento(id):
    try:
        # 1. Busca a venda com bloqueio de linha (Pessimistic Locking)
        venda = Transacao.query.with_for_update().get_or_404(id)

        if venda.status != status_to_value(TransactionStatus.ANALISE):
            flash('Esta transação já foi processada ou não está em análise.', 'warning')
            return redirect(url_for('admin_dashboard.dashboard'))

        # 2. Atualização do Status
        venda.mudar_status(status_to_value(TransactionStatus.ESCROW), "Pagamento validado pelo Admin")

        # 3. Registo de Auditoria
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="VALIDACAO_PAGAMENTO",
            detalhes=f"Ref {venda.fatura_ref} aprovada.",
            ip=request.remote_addr
        ))
        
        # Notificar Produtor
        db.session.add(Notificacao(
            usuario_id=venda.vendedor_id,
            mensagem=f"💰 Pagamento confirmado para {venda.fatura_ref}! Pode enviar a mercadoria.",
            link=url_for('produtor.vendas')
        ))

        # 4. Commit primeiro para garantir que os dados estão salvos antes da tarefa começar
        db.session.commit()

        # 5. DISPARO ASSÍNCRONO (Se configurado)
        try:
            # Tenta agendar email se o scheduler estiver ativo
            if scheduler.running:
                from app.tasks import enviar_fatura_email # Importação lazy
                scheduler.add_job(
                    id=f'envio_fatura_{venda.id}',
                    func=enviar_fatura_email,
                    args=[venda.id],
                    trigger='date',
                    run_date=None
                )
        except Exception as e:
            current_app.logger.warning(f"Falha ao agendar email: {e}")

        flash(f'Pagamento {venda.fatura_ref} validado! O produtor foi notificado.', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO_ADMIN_VALIDACAO (ID: {id}): {e}")
        flash('Erro técnico ao processar a validação.', 'danger')

    return redirect(url_for('admin_dashboard.dashboard'))

@admin_bp.route('/confirmar-transferencia/<int:id>', methods=['POST'])
@login_required
@admin_required
def confirmar_transferencia(id):
    """O Admin confirma que já fez a transferência bancária para o IBAN do produtor e LIBERA o saldo."""
    try:
        venda = Transacao.query.with_for_update().get_or_404(id)

        # Só pode transferir se já foi entregue e ainda não foi finalizado
        if venda.status == status_to_value(TransactionStatus.ENTREGUE) and not venda.transferencia_concluida:
            # 1. Mudar status para FINALIZADO
            venda.transferencia_concluida = True
            venda.mudar_status(status_to_value(TransactionStatus.FINALIZADO), "Transferência aprovada pelo Admin")
            venda.data_liquidacao = datetime.now(timezone.utc)
            
            # 2. LIBERTAR SALDO AO PRODUTOR (só agora!)
            vendedor = venda.vendedor
            valor_liquido = Decimal(str(venda.valor_liquido_vendedor))
            vendedor.saldo_disponivel = (vendedor.saldo_disponivel or Decimal('0.00')) + valor_liquido
            vendedor.vendas_concluidas = (vendedor.vendas_concluidas or 0) + 1
            
            # 3. Registo de Auditoria
            db.session.add(LogAuditoria(
                usuario_id=current_user.id,
                acao="LIQUIDACAO_PRODUTOR",
                detalhes=f"Ref {venda.fatura_ref} liquidada. Valor: {valor_liquido} Kz",
                ip=request.remote_addr
            ))

            # 4. Notifica o Produtor sobre o dinheiro na conta
            db.session.add(Notificacao(
                usuario_id=venda.vendedor_id,
                mensagem=f"💵 Transferência aprovada! Saldo de {valor_liquido} Kz disponível (Ref: {venda.fatura_ref}).",
                link=url_for('produtor.dashboard')
            ))

            db.session.commit()
            flash(f"Transferência aprovada! Saldo de {valor_liquido} Kz libertado ao produtor.", "success")
        else:
            flash("Esta transação não está pronta para liquidação.", "warning")
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO LIQUIDACAO: {e}")
        flash("Erro ao processar liquidação.", "danger")

    return redirect(url_for('admin_dashboard.dashboard'))


# --- GESTÃO DE DISPUTAS ---
@admin_bp.route('/resolver-disputa/<int:trans_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def resolver_disputa(trans_id):
    """Juiz do Mercado: Decide se devolve o dinheiro ao comprador ou paga ao produtor."""
    venda = Transacao.query.get_or_404(trans_id)

    if request.method == 'POST':
        try:
            decisao = request.form.get('decisao')  # 'libertar' ou 'reembolsar'

            if decisao == 'libertar':
                # Paga ao produtor (como se tivesse sido entregue)
                venda.mudar_status(status_to_value(TransactionStatus.ENTREGUE), "Disputa resolvida a favor do Produtor")
                # Creditar saldo ao produtor para ele poder levantar
                produtor = venda.vendedor
                valor_liquido = Decimal(str(venda.valor_liquido_vendedor))
                produtor.saldo_disponivel = (produtor.saldo_disponivel or Decimal('0.00')) + valor_liquido
                
                msg = "Disputa resolvida a favor do Produtor."
                
                db.session.add(Notificacao(usuario_id=venda.vendedor_id, mensagem="✅ Disputa ganha! Fundos libertados."))
                db.session.add(Notificacao(usuario_id=venda.comprador_id, mensagem="❌ Disputa fechada a favor do vendedor."))

            elif decisao == 'reembolsar':
                # Devolve ao comprador
                venda.mudar_status(status_to_value(TransactionStatus.CANCELADO), "Disputa resolvida com Reembolso")
                if venda.safra:
                    venda.safra.quantidade_disponivel += venda.quantidade_comprada
                
                msg = "Disputa resolvida com Reembolso ao Comprador."
                
                db.session.add(Notificacao(usuario_id=venda.comprador_id, mensagem="✅ Disputa ganha! Reembolso aprovado."))
                db.session.add(Notificacao(usuario_id=venda.vendedor_id, mensagem="❌ Disputa fechada a favor do comprador."))

            db.session.add(LogAuditoria(
                usuario_id=current_user.id,
                acao="RESOLUCAO_DISPUTA",
                detalhes=f"Ref {venda.fatura_ref}: {msg}",
                ip=request.remote_addr
            ))
            db.session.commit()
            flash("Disputa encerrada.", "success")
            return redirect(url_for('admin_dashboard.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro disputa: {e}")
            flash("Erro ao resolver disputa.", "danger")

    return render_template('admin/detalhe_disputa.html', venda=venda)


# --- RELATÓRIOS E EXPORTAÇÃO ---
@admin_bp.route('/exportar-financeiro-agro')
@login_required
@admin_required
def exportar_financeiro():
    """Gera um relatório financeiro de nível executivo para instituições."""
    vendas = Transacao.query.all()

    # 1. Estruturação dos dados com lógica de negócio clara
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

    df = pd.DataFrame(dados_vendas)
    output = BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dashboard_Financeiro', startrow=5)

        workbook = writer.book
        worksheet = writer.sheets['Dashboard_Financeiro']

        # --- DICIONÁRIO DE FORMATOS ---
        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#1B4332', 'font_color': 'white',
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 11
        })

        money_fmt = workbook.add_format({'num_format': '#,##0.00" Kz"', 'border': 1, 'font_size': 10})
        date_fmt = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1, 'align': 'center'})
        text_fmt = workbook.add_format({'border': 1, 'font_size': 10})
        title_fmt = workbook.add_format({'bold': True, 'font_size': 18, 'font_color': '#1B4332'})
        label_fmt = workbook.add_format({'bold': True, 'bg_color': '#F8F9FA', 'border': 1})

        # 2. CABEÇALHO CORPORATIVO
        worksheet.write('A1', 'AGROKONGO - RELATÓRIO DE CONCILIAÇÃO FINANCEIRA', title_fmt)
        worksheet.write('A2', f'Período: Até {datetime.now().strftime("%d/%m/%Y")}')
        worksheet.write('A3', 'Finalidade: Instrução de Transferência / Auditoria AGT')

        # 3. SUMÁRIO DE TOTAIS NO TOPO (Acesso Rápido)
        worksheet.write('F3', 'TOTAL EM CUSTÓDIA', label_fmt)
        worksheet.write_formula('G3', f'=SUM(G6:G{len(dados_vendas) + 6})', money_fmt)

        worksheet.write('H3', 'LÍQUIDO A PAGAR', label_fmt)
        worksheet.write_formula('I3', f'=SUM(I6:I{len(dados_vendas) + 6})', money_fmt)

        # 4. FORMATAÇÃO DA TABELA
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(5, col_num, value, header_fmt)

        # Ajuste de larguras para legibilidade
        worksheet.set_column('A:A', 14, text_fmt)  # ID
        worksheet.set_column('B:B', 14, date_fmt)  # Data
        worksheet.set_column('C:C', 16, text_fmt)  # Ref
        worksheet.set_column('D:D', 30, text_fmt)  # Produtor
        worksheet.set_column('E:E', 15, text_fmt)  # NIF
        worksheet.set_column('F:F', 28, text_fmt)  # IBAN
        worksheet.set_column('G:I', 20, money_fmt)  # Valores
        worksheet.set_column('J:J', 20, text_fmt)  # Status

        # 5. DESTAQUE VISUAL (Formatação Condicional)
        worksheet.conditional_format(6, 9, len(dados_vendas) + 6, 9, {
            'type': 'cell', 'criteria': 'containing', 'value': 'PAGO',
            'format': workbook.add_format({'bg_color': '#DFF0D8', 'font_color': '#3C763D'})
        })

    output.seek(0)
    return send_file(output, as_attachment=True,
                     download_name=f"AGROKONGO_FINANCEIRO_{datetime.now().strftime('%d_%m_%Y')}.xlsx")


# --- UTILITÁRIOS DE SERVIDOR ---
@admin_bp.route('/ver-comprovativo/<path:filename>')
@login_required
@admin_required
def ver_comprovativo(filename):
    """Acesso seguro a ficheiros privados (Talões)."""
    # Remove prefixos duplicados se existirem
    filename = filename.replace('comprovativos/', '')
    folder = os.path.join(current_app.config['UPLOAD_FOLDER_PRIVATE'], 'comprovativos')
    return send_from_directory(folder, filename)


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

# --- VALIDAÇÃO DE UTILIZADOR ---
@admin_bp.route('/validar-usuario/<int:user_id>', methods=['POST'])
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
        
    return redirect(url_for('admin.lista_usuarios'))


# --- REJEIÇÃO DE UTILIZADOR ---
@admin_bp.route('/rejeitar-usuario/<int:user_id>', methods=['POST'])
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
        
    return redirect(url_for('admin.detalhes_usuario', user_id=user.id))


# --- LISTA DE UTILIZADORES ---
@admin_bp.route('/usuarios')
@login_required
@admin_required
def lista_usuarios():
    usuarios = Usuario.query.filter(Usuario.tipo != 'admin').order_by(Usuario.nome).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)


# --- PAGAMENTOS PENDENTES AO PRODUTOR ---
@admin_bp.route('/pagamentos-pendentes')
@login_required
@admin_required
def pagamentos_pendentes():
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
        'vendas_concluidas': 0,
        'total_gasto': Decimal('0.00') # Inicialização segura
    }

    if user.tipo == 'produtor':
        # Histórico de Vendas
        transacoes = Transacao.query.filter_by(vendedor_id=user.id).order_by(Transacao.data_criacao.desc()).all()

        # Soma do que já foi efetivamente pago (Status FINALIZADO/CONCLUIDO)
        stats['total_faturado'] = db.session.query(func.sum(Transacao.valor_liquido_vendedor)).filter(
            Transacao.vendedor_id == user.id,
            Transacao.transferencia_concluida == True
        ).scalar() or Decimal('0.00')

        # Soma do que está "preso" aguardando liquidação (Status ESCROW/ENTREGUE)
        stats['em_custodia'] = db.session.query(func.sum(Transacao.valor_liquido_vendedor)).filter(
            Transacao.vendedor_id == user.id,
            Transacao.status.in_([status_to_value(TransactionStatus.ESCROW), status_to_value(TransactionStatus.ENVIADO), status_to_value(TransactionStatus.ENTREGUE)]),
            Transacao.transferencia_concluida == False
        ).scalar() or Decimal('0.00')

        stats['vendas_concluidas'] = Transacao.query.filter_by(vendedor_id=user.id,
                                                               transferencia_concluida=True).count()

    else:
        # Histórico de Compras para Compradores
        transacoes = Transacao.query.filter_by(comprador_id=user.id).order_by(Transacao.data_criacao.desc()).all()
        stats['total_gasto'] = db.session.query(func.sum(Transacao.valor_total_pago)).filter_by(
            comprador_id=user.id).scalar() or Decimal('0.00')

    # 2. LOGS DE AUDITORIA (Busca inteligente por Nome, NIF ou ID direto)
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
    try:
        venda = Transacao.query.get_or_404(id)
        motivo = request.form.get('motivo', 'Não especificado')

        # REGISTO DE LOG
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="REJEICAO_PAGAMENTO",
            detalhes=f"Rejeitou pagamento da Ref: {venda.fatura_ref}. Motivo: {motivo}",
            ip=request.remote_addr
        ))

        venda.status = TransactionStatus.PENDENTE # Volta ao início ou a AGUARDANDO_PAGAMENTO?
        # Normalmente volta a 'AGUARDANDO_PAGAMENTO' se o erro for apenas no comprovativo
        # Mas 'pendente' força o comprador a recomeçar o upload.
        # Ajuste para manter consistência:
        venda.status = TransactionStatus.AGUARDANDO_PAGAMENTO 
        
        # Apagar comprovativo inválido (opcional, pode manter para prova)
        venda.comprovativo_path = None

        db.session.add(Notificacao(
            usuario_id=venda.comprador_id,
            mensagem=f"❌ Pagamento Rejeitado ({venda.fatura_ref}). Motivo: {motivo}. Envie novo comprovativo.",
            link=url_for('comprador.dashboard')
        ))

        db.session.commit()
        flash('Pagamento rejeitado e log registado.', 'info')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro rejeitar pagamento: {e}")
        flash("Erro ao rejeitar pagamento.", "danger")

    return redirect(url_for('admin_dashboard.dashboard'))


@admin_bp.route('/historico-financeiro')
@login_required
@admin_required
def historico_financeiro():
    # 1. Talões validados
    taloes_validados = Transacao.query.filter(
        Transacao.status.in_([status_to_value(TransactionStatus.ESCROW), status_to_value(TransactionStatus.ENVIADO), status_to_value(TransactionStatus.ENTREGUE), status_to_value(TransactionStatus.FINALIZADO)])
    ).order_by(Transacao.data_criacao.desc()).all()

    # 2. Transferências feitas para produtores
    liquidacoes_concluidas = Transacao.query.filter_by(transferencia_concluida=True)\
        .order_by(Transacao.data_criacao.desc()).all()

    return render_template('admin/historico_financeiro.html',
                           taloes=taloes_validados,
                           liquidacoes=liquidacoes_concluidas)

@admin_bp.route('/detalhe-transacao/<int:id>')
@login_required
@admin_required
def detalhe_transacao(id):
    transacao = Transacao.query.get_or_404(id)
    return render_template('admin/detalhe_transacao.html', t=transacao)

# --- GERIR TALÕES ---
@admin_bp.route('/gerir-taloes')
@login_required
@admin_required
def gerir_taloes():
    # Filtros usando estritamente os Enums
    pendentes = Transacao.query.filter_by(status=status_to_value(TransactionStatus.ANALISE)).all()

    validados = Transacao.query.filter(
        Transacao.status.in_([
            status_to_value(TransactionStatus.ESCROW),
            status_to_value(TransactionStatus.ENVIADO),
            status_to_value(TransactionStatus.ENTREGUE),
            status_to_value(TransactionStatus.FINALIZADO)
        ])
    ).order_by(Transacao.data_criacao.desc()).all()

    return render_template('admin/gerir_taloes.html', pendentes=pendentes, validados=validados)


@admin_bp.route('/liquidar-pagamento/<int:trans_id>', methods=['POST'])
@login_required
@admin_required
def liquidar_pagamento(trans_id):
    # ATENÇÃO: Esta rota é redundante com 'confirmar_transferencia'. 
    # Mantenho a lógica mas redireciono ou unifico o comportamento.
    return confirmar_transferencia(trans_id)


@admin_bp.route('/painel-pagamentos')
@login_required
@admin_required
def painel_pagamentos():
    # Buscamos apenas o que está 'ENTREGUE' mas ainda não foi transferido
    pendentes_liquidacao = Transacao.query.filter_by(
        status=status_to_value(TransactionStatus.ENTREGUE),
        transferencia_concluida=False
    ).all()

    return render_template('admin/painel_pagamentos.html', pendentes=pendentes_liquidacao)


@admin_bp.route('/tesouraria')
@login_required
@admin_required
def painel_liquidacoes():
    # Apenas o que o comprador já recebeu, mas o produtor ainda não recebeu o dinheiro
    vendas_pendentes = Transacao.query.filter_by(
        status=status_to_value(TransactionStatus.ENTREGUE),
        transferencia_concluida=False
    ).all()

    return render_template('admin/pagamentos.html', vendas=vendas_pendentes)


@admin_bp.route('/usuario/eliminar/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def eliminar_usuario(user_id):
    try:
        usuario = Usuario.query.get_or_404(user_id)

        # 1. Limpeza de Ficheiros Físicos
        if usuario.foto_perfil:
            caminho_foto = os.path.join(current_app.config['UPLOAD_FOLDER_PUBLIC'], 'perfil', usuario.foto_perfil)
            if os.path.exists(caminho_foto):
                try: os.remove(caminho_foto)
                except: pass

        if usuario.documento_pdf:
            caminho_pdf = os.path.join(current_app.config['UPLOAD_FOLDER_PRIVATE'], 'documentos', usuario.documento_pdf)
            if os.path.exists(caminho_pdf):
                try: os.remove(caminho_pdf)
                except: pass

        # 2. Eliminar da Base de Dados
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

    return redirect(url_for('admin.lista_usuarios'))