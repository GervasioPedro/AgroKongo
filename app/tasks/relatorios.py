# app/tasks/relatorios.py - Versão auditada, profissional e escalável
# Versão Corrigida - 26/02/2026
from celery import shared_task
import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO
import os
import hashlib
from datetime import datetime, timedelta, timezone
from flask import url_for
from app.extensions import db, current_app, cache
from app.tasks.base import AgroKongoTask
from app.models import (
    Usuario, LogAuditoria, Notificacao, Transacao, TransactionStatus,
    Produto, Safra
)
from app.utils.helpers import aware_utcnow, formatar_moeda_kz
from sqlalchemy import func
from decimal import Decimal


@shared_task(bind=True, base=AgroKongoTask, max_retries=5, rate_limit='3/h')
def gerar_relatorio_excel_assincrono(self, admin_id: int, periodo: str = None):
    """
    Gera Excel async relatório financeiro completo.
    Segurança: admin only, path privado, hash.
    UX: múltiplos sheets formatados moeda Kz, top produtos tabela.
    Retorna path para download route.
    """
    try:
        _validar_admin(admin_id)
        start_date, end_date = _validar_periodo(periodo)
        relatorio = _gerar_dados_relatorio(start_date, end_date)
        excel_bytes = _gerar_excel_content(relatorio)
        path = _salvar_excel_seguro(excel_bytes, periodo)
        _notificar_relatorio_pronto(admin_id, periodo, path)
        return path

    except (PermissionError, ValueError) as e:
        current_app.logger.warning(f"Erro lógico relatório admin {admin_id}: {e}")
        _notificar_erro_relatorio(admin_id, e)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro task relatório admin {admin_id}: {e}", exc_info=True)
        raise self.retry(exc=e)

    return None


def _validar_admin(admin_id):
    """Valida se usuário é administrador."""
    admin = db.session.query(Usuario).get(admin_id)
    if not admin or admin.tipo != 'admin':
        raise PermissionError("Acesso negado ao relatório.")


def _validar_periodo(periodo):
    """Valida e retorna datas de início e fim do período."""
    if periodo:
        try:
            ano, mes = map(int, periodo.split('-'))
            start_date = datetime(ano, mes, 1, tzinfo=timezone.utc)
            if mes == 12:
                end_date = datetime(ano + 1, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
            else:
                end_date = datetime(ano, mes + 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
        except (ValueError, IndexError):
            raise ValueError("Período inválido (YYYY-MM).")
    else:
        start_date = aware_utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = aware_utcnow()
    return start_date, end_date


def _gerar_excel_content(relatorio):
    """Gera conteúdo Excel com múltiplos sheets."""
    buffer = BytesIO()
    try:
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_resumo = pd.DataFrame({
                'Métrica': [
                    'Total Escrow (Kz)',
                    'Lucro Plataforma (Kz)',
                    'Transações Totais',
                    'Disputas',
                    'Novos Usuários',
                    'Novos Produtores',
                    'Novos Compradores',
                    'Crescimento Usuários (%)',
                    'Período'
                ],
                'Valor': [
                    formatar_moeda_kz(relatorio['total_escrow']),
                    formatar_moeda_kz(relatorio['lucro_plataforma']),
                    relatorio['transacoes_totais'],
                    relatorio['disputas'],
                    relatorio['novos_usuarios'],
                    relatorio['novos_produtores'],
                    relatorio['novos_compradores'],
                    f"{relatorio['crescimento_usuarios_pct']}%",
                    relatorio['periodo']
                ]
            })
            df_resumo.to_excel(writer, sheet_name='Resumo', index=False)
            worksheet = writer.sheets['Resumo']
            worksheet.column_dimensions['A'].width = 35
            worksheet.column_dimensions['B'].width = 25

            if relatorio['top_produtos']:
                df_top = pd.DataFrame(relatorio['top_produtos'])
                df_top.to_excel(writer, sheet_name='Top Produtos', index=False)
                ws_top = writer.sheets['Top Produtos']
                ws_top.column_dimensions['A'].width = 40
                ws_top.column_dimensions['B'].width = 20

        buffer.seek(0)
        return buffer.getvalue()
    finally:
        buffer.close()


def _salvar_excel_seguro(excel_bytes, periodo):
    """Salva Excel com hash de integridade e path seguro."""
    hash_excel = hashlib.sha256(excel_bytes).hexdigest()
    
    subpasta = 'relatorios'
    # Validação contra path traversal na subpasta
    if '..' in subpasta or '/' in subpasta or '\\' in subpasta:
        raise ValueError("Path traversal detectado: subpasta inválida")
    if subpasta not in ['relatorios', 'faturas', 'fotos']:
        raise ValueError("Subpasta inválida")
    
    # Validação do período antes de usar
    if periodo and ('..' in periodo or '/' in periodo or '\\' in periodo):
        raise ValueError("Período inválido: caracteres perigosos")
    
    safe_periodo = os.path.basename(periodo or 'completo')
    filename = f"relatorio_{safe_periodo}_{aware_utcnow().strftime('%Y%m%d')}_{hash_excel[:8]}.xlsx"
    safe_filename = os.path.basename(filename)
    
    # Validação adicional contra caracteres perigosos
    if '..' in safe_filename or '/' in safe_filename or '\\' in safe_filename:
        raise ValueError("Path traversal detectado: caracteres inválidos")
    
    base_dir = os.path.abspath(os.path.join(current_app.config['UPLOAD_FOLDER_PRIVATE'], subpasta))
    path = os.path.abspath(os.path.join(base_dir, safe_filename))
    
    # Verificação robusta de path traversal
    if not path.startswith(base_dir + os.sep):
        raise ValueError("Path traversal detectado: caminho fora do diretório permitido")
    
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    with open(path, 'wb') as f:
        f.write(excel_bytes)
    
    return path


def _notificar_relatorio_pronto(admin_id, periodo, path):
    """Cria notificação e auditoria de relatório pronto."""
    safe_filename = os.path.basename(path)
    hash_excel = safe_filename.split('_')[-1].replace('.xlsx', '')
    
    db.session.add(Notificacao(
        usuario_id=admin_id,
        mensagem=f"📊 Relatório Excel {periodo or 'completo'} pronto! Baixe aqui.",
        link=f"/admin/download-relatorio/{safe_filename}"
    ))
    
    db.session.add(LogAuditoria(
        usuario_id=admin_id,
        acao="GEROU_RELATORIO_EXCEL",
        detalhes=f"Relatório {periodo or 'completo'} salvo (hash: {hash_excel})",
        ip="celery_task"
    ))
    db.session.commit()


def _notificar_erro_relatorio(admin_id, erro):
    """Notifica administrador sobre erro na geração do relatório."""
    db.session.add(Notificacao(
        usuario_id=admin_id,
        mensagem=f"❌ Erro geração relatório: {str(erro)[:100]}",
        link="/admin/dashboard"
    ))
    db.session.commit()


def _gerar_dados_relatorio(start_date, end_date):
    """
    Gera dados do relatório financeiro (função auxiliar).
    """
    # Escrow atual
    total_escrow = db.session.query(
        func.coalesce(func.sum(Transacao.valor_total_pago), Decimal('0.00'))
    ).filter(
        Transacao.status == TransactionStatus.ANALISE,
        Transacao.data_criacao <= end_date
    ).scalar() or Decimal('0.00')

    # Comissões plataforma (FINALIZADO no período)
    total_comissoes = db.session.query(
        func.coalesce(func.sum(Transacao.comissao_plataforma), Decimal('0.00'))
    ).filter(
        Transacao.status == TransactionStatus.FINALIZADO,
        Transacao.data_liquidacao.between(start_date, end_date)
    ).scalar() or Decimal('0.00')

    # Novos usuários validados
    novos_usuarios = Usuario.query.filter(
        Usuario.data_cadastro.between(start_date, end_date),
        Usuario.conta_validada is True
    ).count()

    novos_produtores = Usuario.query.filter(
        Usuario.data_cadastro.between(start_date, end_date),
        Usuario.conta_validada is True,
        Usuario.tipo == 'produtor'
    ).count()

    novos_compradores = novos_usuarios - novos_produtores

    # Crescimento vs período anterior
    duracao = end_date - start_date
    prev_start = start_date - duracao
    prev_end = start_date - timedelta(seconds=1)
    novos_prev = Usuario.query.filter(
        Usuario.data_cadastro.between(prev_start, prev_end),
        Usuario.conta_validada is True
    ).count()
    crescimento = round(((novos_usuarios - novos_prev) / novos_prev * 100) if novos_prev > 0 else 0, 2)

    # Transações totais e disputas
    transacoes_totais = Transacao.query.filter(
        Transacao.data_criacao.between(start_date, end_date)
    ).count()

    disputas = Transacao.query.filter(
        Transacao.status == TransactionStatus.DISPUTA,
        Transacao.data_criacao.between(start_date, end_date)
    ).count()

    # Top 5 produtos
    top_produtos = db.session.query(
        Produto.nome.label('produto'),
        func.sum(Transacao.quantidade_comprada).label('volume')
    ).join(
        Safra, Transacao.safra_id == Safra.id
    ).join(
        Produto, Safra.produto_id == Produto.id
    ).filter(
        Transacao.status == TransactionStatus.FINALIZADO,
        Transacao.data_liquidacao.between(start_date, end_date)
    ).group_by(
        Produto.nome
    ).order_by(
        func.sum(Transacao.quantidade_comprada).desc()
    ).limit(5).all()

    return {
        'total_escrow': total_escrow,
        'lucro_plataforma': total_comissoes,
        'transacoes_totais': transacoes_totais,
        'disputas': disputas,
        'novos_usuarios': novos_usuarios,
        'novos_produtores': novos_produtores,
        'novos_compradores': novos_compradores,
        'crescimento_usuarios_pct': crescimento,
        'top_produtos': [
            {'Produto': p.produto, 'Volume (kg)': float(p.volume or 0)}
            for p in top_produtos
        ],
        'periodo': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
        'gerado_em': aware_utcnow().strftime('%d/%m/%Y %H:%M')
    }