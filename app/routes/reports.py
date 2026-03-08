# app/routes/reports.py - Relatórios financeiros cacheados e seguros (admin only)
# Versão Corrigida - 22/02/2026
from flask import Blueprint, render_template, current_app
from flask_login import login_required
from app.extensions import cache, db
from app.models import Transacao, Usuario, TransactionStatus, Produto, Safra
from app.utils.decorators import admin_required
from app.models.base import aware_utcnow
from sqlalchemy import func
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import hashlib

reports_bp = Blueprint('reports', __name__)  # ← Corrigido de 'name' para '__name__'


@reports_bp.route('/relatorio')
@login_required
@admin_required
def relatorio():
    """Página de relatório financeiro (admin only)."""
    data = obter_relatorio_financeiro()
    return render_template('admin/relatorio.html', data=data)


def cache_key_relatorio(start_date, end_date):  # ← Corrigido de '_cache_key_relatorio'
    """Key dinâmica com hash período."""
    period_str = f"{start_date.isoformat()}{end_date.isoformat()}"
    return f"relatorio_financeiro_{hashlib.sha256(period_str.encode()).hexdigest()[:12]}"


@cache.cached(timeout=600, key_prefix=cache_key_relatorio)
def obter_relatorio_financeiro(start_date=None, end_date=None):
    """
    Relatório financeiro consolidado global (admin only).
    Cache por período, invalidação via listener.
    """
    try:
        start_date, end_date = _validar_datas_relatorio(start_date, end_date)
        metricas_financeiras = _calcular_metricas_financeiras(start_date, end_date)
        metricas_usuarios = _calcular_metricas_usuarios(start_date, end_date)
        top_produtos = _obter_top_produtos(start_date, end_date)
        
        return _montar_relatorio(metricas_financeiras, metricas_usuarios, top_produtos, start_date, end_date)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"DB erro relatório: {e}")
        return {}


def _validar_datas_relatorio(start_date, end_date):
    """Valida e retorna datas padrão se não fornecidas."""
    agora = aware_utcnow()
    if start_date is None:
        start_date = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if end_date is None:
        end_date = agora
    return start_date, end_date


def _calcular_metricas_financeiras(start_date, end_date):
    """Calcula métricas financeiras do período."""
    total_escrow = db.session.query(
        func.coalesce(func.sum(Transacao.valor_total_pago), Decimal('0.00'))
    ).filter(
        Transacao.status == TransactionStatus.ANALISE,
        Transacao.data_criacao <= end_date
    ).scalar()

    total_comissoes = db.session.query(
        func.coalesce(func.sum(Transacao.comissao_plataforma), Decimal('0.00'))
    ).filter(
        Transacao.status == TransactionStatus.FINALIZADO,
        Transacao.data_liquidacao.between(start_date, end_date)
    ).scalar()

    transacoes_totais = Transacao.query.filter(
        Transacao.data_criacao.between(start_date, end_date)
    ).count()

    disputas = Transacao.query.filter(
        Transacao.status == TransactionStatus.DISPUTA,
        Transacao.data_criacao.between(start_date, end_date)
    ).count()

    return {
        'total_escrow': total_escrow.quantize(Decimal('0.00')),
        'lucro_plataforma': total_comissoes.quantize(Decimal('0.00')),
        'transacoes_totais': transacoes_totais,
        'disputas': disputas
    }


def _calcular_metricas_usuarios(start_date, end_date):
    """Calcula métricas de usuários do período."""
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

    duracao = end_date - start_date
    prev_start = start_date - duracao
    prev_end = start_date - timedelta(seconds=1)
    novos_prev = Usuario.query.filter(
        Usuario.data_cadastro.between(prev_start, prev_end),
        Usuario.conta_validada is True
    ).count()
    crescimento = round(((novos_usuarios - novos_prev) / novos_prev * 100) if novos_prev else 100, 2)

    return {
        'novos_usuarios': novos_usuarios,
        'novos_produtores': novos_produtores,
        'novos_compradores': novos_compradores,
        'crescimento_usuarios_pct': crescimento
    }


def _obter_top_produtos(start_date, end_date):
    """Obtém top 5 produtos por volume vendido."""
    top_produtos = db.session.query(
        func.coalesce(Produto.nome, 'Desconhecido').label('produto'),
        func.coalesce(func.sum(Transacao.quantidade_comprada), Decimal('0')).label('volume')
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

    return [{'produto': p.produto, 'volume': float(p.volume)} for p in top_produtos]


def _montar_relatorio(metricas_financeiras, metricas_usuarios, top_produtos, start_date, end_date):
    """Monta dicionário final do relatório."""
    agora = aware_utcnow()
    return {
        **metricas_financeiras,
        **metricas_usuarios,
        'top_produtos': top_produtos,
        'periodo': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
        'gerado_em': agora.strftime('%d/%m/%Y %H:%M')
    }


# Listener invalidação cache (mova para models.py ou __init__.py)
from sqlalchemy.event import listens_for


@listens_for(Transacao, 'after_insert')
@listens_for(Transacao, 'after_update')
@listens_for(Transacao, 'after_delete')
def invalidate_relatorio_cache(mapper, connection, target):
    """Invalida cache de relatórios quando transações mudam."""
    # Opção 1: Limpar tudo (simples)
    # cache.clear()

    # Opção 2: Limpar apenas relatórios (recomendado com Redis)
    try:
        cache.delete_matched('relatorio_financeiro_*')
    except AttributeError:
        # Fallback se Redis não suportar delete_matched
        cache.clear()