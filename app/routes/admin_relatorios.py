"""
Blueprint para relatórios e exportação de dados do Admin.
Responsável por geração de Excel, PDF e métricas executivas.
"""
import os
import pandas as pd
from io import BytesIO
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models import Transacao, Usuario, Safra, Produto, TransactionStatus, LogAuditoria
from functools import wraps

admin_relatorios_bp = Blueprint('admin_relatorios', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != 'admin':
            flash("Acesso restrito a administradores.", "danger")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_relatorios_bp.route('/exportar-financeiro-agro')
@login_required
@admin_required
def exportar_financeiro():
    """Gera um relatório financeiro de nível executivo para instituições."""
    vendas = Transacao.query.all()

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

        # DICIONÁRIO DE FORMATOS
        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#1B4332', 'font_color': 'white',
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 11
        })

        money_fmt = workbook.add_format({'num_format': '#,##0.00" Kz"', 'border': 1, 'font_size': 10})
        date_fmt = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1, 'align': 'center'})
        text_fmt = workbook.add_format({'border': 1, 'font_size': 10})
        title_fmt = workbook.add_format({'bold': True, 'font_color': '#1B4332', 'font_size': 18})
        label_fmt = workbook.add_format({'bold': True, 'bg_color': '#F8F9FA', 'border': 1})

        # CABEÇALHO CORPORATIVO
        worksheet.write('A1', 'AGROKONGO - RELATÓRIO DE CONCILIAÇÃO FINANCEIRA', title_fmt)
        worksheet.write('A2', f'Período: Até {datetime.now().strftime("%d/%m/%Y")}')
        worksheet.write('A3', 'Finalidade: Instrução de Transferência / Auditoria AGT')

        # SUMÁRIO DE TOTAIS NO TOPO
        worksheet.write('F3', 'TOTAL EM CUSTÓDIA', label_fmt)
        worksheet.write_formula('G3', f'=SUM(G6:G{len(dados_vendas) + 6})', money_fmt)

        worksheet.write('H3', 'LÍQUIDO A PAGAR', label_fmt)
        worksheet.write_formula('I3', f'=SUM(I6:I{len(dados_vendas) + 6})', money_fmt)

        # FORMATAÇÃO DA TABELA
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(5, col_num, value, header_fmt)

        # Ajuste de larguras
        worksheet.set_column('A:A', 14, text_fmt)
        worksheet.set_column('B:B', 14, date_fmt)
        worksheet.set_column('C:C', 16, text_fmt)
        worksheet.set_column('D:D', 30, text_fmt)
        worksheet.set_column('E:E', 15, text_fmt)
        worksheet.set_column('F:F', 28, text_fmt)
        worksheet.set_column('G:I', 20, money_fmt)
        worksheet.set_column('J:J', 20, text_fmt)

        # DESTAQUE VISUAL
        worksheet.conditional_format(6, 9, len(dados_vendas) + 6, 9, {
            'type': 'cell', 'criteria': 'containing', 'value': 'PAGO',
            'format': workbook.add_format({'bg_color': '#DFF0D8', 'font_color': '#3C763D'})
        })

    output.seek(0)
    return send_file(output, as_attachment=True,
                     download_name=f"AGROKONGO_FINANCEIRO_{datetime.now().strftime('%d_%m_%Y')}.xlsx")


@admin_relatorios_bp.route('/logs')
@login_required
@admin_required
def logs():
    lista_logs = LogAuditoria.query.order_by(LogAuditoria.data_criacao.desc()).limit(100).all()
    return render_template('admin/logs.html', logs=lista_logs)


@admin_relatorios_bp.route('/detalhe-transacao/<int:id>')
@login_required
@admin_required
def detalhe_transacao(id):
    transacao = Transacao.query.get_or_404(id)
    return render_template('admin/detalhe_transacao.html', t=transacao)


@admin_relatorios_bp.route('/ver-comprovativo/<path:filename>')
@login_required
@admin_required
def ver_comprovativo(filename):
    """Acesso seguro a ficheiros privados (Talões)."""
    filename = filename.replace('comprovativos/', '')
    folder = os.path.join(current_app.config['UPLOAD_FOLDER_PRIVATE'], 'comprovativos')
    return send_from_directory(folder, filename)
