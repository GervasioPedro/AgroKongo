@produtor_bp.route('/api/produtor/transacoes')
@login_required
@produtor_required
def api_transacoes_produtor():
    """API para listar todas as transações do produtor."""
    transacoes = Transacao.query.filter_by(vendedor_id=current_user.id) \
        .order_by(Transacao.data_criacao.desc()).all()
    
    def transacao_completa(t: Transacao):
        return {
            'id': t.id,
            'fatura_ref': t.fatura_ref,
            'status': t.status,
            'safra': {
                'produto': getattr(getattr(t.safra, 'produto', None), 'nome', 'Produto')
            },
            'quantidade_comprada': float(t.quantidade_comprada) if t.quantidade_comprada else 0,
            'valor_total_pago': float(t.valor_total_pago) if t.valor_total_pago else 0,
            'data_criacao': t.data_criacao.isoformat() if t.data_criacao else None,
            'comprador': {
                'nome': getattr(t.comprador, 'nome', 'Comprador')
            }
        }
    
    return jsonify({
        'transacoes': [transacao_completa(t) for t in transacoes]
    })
