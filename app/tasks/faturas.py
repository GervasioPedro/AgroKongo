# app/tasks/faturas.py - Versão auditada, segura e completa (produção-ready)
# Versão Corrigida - 22/02/2026
from celery import shared_task
from flask import url_for  # ← Import adicionado
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import qrcode
import hashlib
import os
from flask import current_app
from app.extensions import db
from app.tasks.base import AgroKongoTask, AgroKongoTaskBase  # ← Import adicionado
from app.models import Transacao, Usuario, LogAuditoria, Notificacao, Safra  # ← Safra adicionado
from app.models.base import aware_utcnow
import bleach
from sqlalchemy.orm import joinedload  # ← Import adicionado


@shared_task(bind=True, base=AgroKongoTaskBase, max_retries=5, rate_limit='5/m')
def gerar_pdf_fatura_assincrono(self, trans_id: str, user_id: int):
    """
    Gera PDF fatura async com QR validação, hash integridade.
    Segurança: ownership, sanitização, path seguro.
    UX: layout mobile, QR escaneável, notificação link download.
    Retorna path para download route.
    """
    try:
        transacao, user = _carregar_dados_fatura(trans_id, user_id)
        pdf_bytes = _gerar_pdf_content(transacao)
        path = _salvar_pdf_seguro(transacao, pdf_bytes)
        _notificar_fatura_pronta(transacao, user_id, path)
        return path

    except (ValueError, PermissionError) as e:
        current_app.logger.warning(f"Erro lógico fatura {trans_id}: {e}")
        _notificar_erro_fatura(trans_id, user_id, e)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro task fatura {trans_id}: {e}", exc_info=True)
        raise self.retry(exc=e)

    return None


def _carregar_dados_fatura(trans_id, user_id):
    """Carrega e valida dados da transação e usuário."""
    transacao = db.session.query(Transacao).options(
        joinedload(Transacao.safra).joinedload(Safra.produto),
        joinedload(Transacao.comprador),
        joinedload(Transacao.vendedor)
    ).get(trans_id)

    if not transacao:
        raise ValueError(f"Transação {trans_id} não encontrada.")

    user = db.session.query(Usuario).get(user_id)
    if user.id not in [transacao.comprador_id, transacao.vendedor_id] and user.tipo != 'admin':
        raise PermissionError("Acesso negado à fatura.")
    
    return transacao, user


def _gerar_pdf_content(transacao):
    """Gera conteúdo PDF da fatura."""
    buffer = BytesIO()
    try:
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
        elements = []
        styles = getSampleStyleSheet()

        # Cabeçalho
        elements.append(Paragraph("Fatura Oficial AgroKongo", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Referência: {transacao.fatura_ref}", styles['Heading2']))
        elements.append(Paragraph(f"Data emissão: {aware_utcnow().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 12))

        # Partes envolvidas (sanitizado)
        data_partes = [
            ['Comprador', bleach.clean(transacao.comprador.nome or 'N/A')],
            ['NIF', transacao.comprador.nif or 'N/A'],
            ['Telemóvel', transacao.comprador.telemovel or 'N/A'],
            ['Vendedor', bleach.clean(transacao.vendedor.nome or 'N/A')],
            ['NIF', transacao.vendedor.nif or 'N/A'],
            ['Telemóvel', transacao.vendedor.telemovel or 'N/A']
        ]
        t = Table(data_partes, colWidths=[100*mm, 80*mm])
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('BACKGROUND', (0,2), (-1,2), colors.lightgrey)
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

        # Detalhes transação
        data_trans = [
            ['Produto', bleach.clean(transacao.safra.produto.nome)],
            ['Quantidade', f"{transacao.quantidade_comprada} {transacao.safra.produto.categoria or 'unidades'}"],
            ['Preço unitário', f"{transacao.safra.preco_por_unidade:.2f} Kz"],
            ['Valor total', f"{transacao.valor_total_pago:.2f} Kz"],
            ['Comissão plataforma', f"{transacao.comissao_plataforma:.2f} Kz"],
            ['Líquido vendedor', f"{transacao.valor_liquido_vendedor:.2f} Kz"]
        ]
        t = Table(data_trans, colWidths=[100*mm, 80*mm])
        t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
        elements.append(t)
        elements.append(Spacer(1, 20))

        # QR Code validação
        qr_url = f"https://{current_app.config.get('SERVER_NAME', 'agrokongo.ao')}/validar-fatura/{transacao.fatura_ref}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        try:
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            elements.append(Paragraph("Escaneie para validar fatura:", styles['Normal']))
            elements.append(Image(qr_buffer, width=80*mm, height=80*mm))
        finally:
            qr_buffer.close()

        doc.build(elements)
        return buffer.getvalue()
    finally:
        buffer.close()


def _salvar_pdf_seguro(transacao, pdf_bytes):
    """Salva PDF com hash de integridade e path seguro."""
    hash_pdf = hashlib.sha256(pdf_bytes).hexdigest()
    
    subpasta = 'faturas'
    
    # Validação da referência antes de usar
    if not transacao.fatura_ref or '..' in transacao.fatura_ref or '/' in transacao.fatura_ref or '\\' in transacao.fatura_ref:
        raise ValueError("Referência de fatura inválida")
    
    safe_ref = os.path.basename(transacao.fatura_ref)
    filename = f"{safe_ref}_{hash_pdf[:8]}.pdf"
    safe_filename = os.path.basename(filename)
    
    # Validação adicional contra caracteres perigosos
    if '..' in safe_filename or '/' in safe_filename or '\\' in safe_filename:
        raise ValueError("Path traversal detectado: caracteres inválidos")
    
    base_dir = os.path.abspath(current_app.config['SUBFOLDERS'][subpasta])
    path = os.path.abspath(os.path.join(base_dir, safe_filename))
    
    # Verificação robusta de path traversal
    if not path.startswith(base_dir + os.sep):
        raise ValueError("Path traversal detectado: caminho fora do diretório permitido")
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(pdf_bytes)
    
    return path


def _notificar_fatura_pronta(transacao, user_id, path):
    """Cria notificação e auditoria de fatura pronta."""
    subpasta = 'faturas'
    safe_filename = os.path.basename(path)
    download_link = url_for('main.servir_arquivo', subpasta=subpasta, filename=safe_filename, _external=True)
    
    db.session.add(Notificacao(
        usuario_id=user_id,
        mensagem=f"Fatura {transacao.fatura_ref} pronta! Baixe aqui.",
        link=download_link
    ))
    
    hash_pdf = os.path.basename(path).split('_')[-1].replace('.pdf', '')
    db.session.add(LogAuditoria(
        usuario_id=user_id,
        acao="GEROU_FATURA_PDF",
        detalhes=f"Fatura {transacao.fatura_ref} salva em {path} (hash: {hash_pdf})"
    ))
    db.session.commit()


def _notificar_erro_fatura(trans_id, user_id, erro):
    """Notifica usuário sobre erro na geração da fatura."""
    try:
        transacao = db.session.query(Transacao).get(trans_id)
        fatura_ref = transacao.fatura_ref if transacao else trans_id
    except:
        fatura_ref = trans_id
    
    db.session.add(Notificacao(
        usuario_id=user_id,
        mensagem=f"Erro geração fatura {fatura_ref}: {str(erro)}"
    ))
    db.session.commit()