"""
Microsserviço de Pagamentos - AgroKongo Payment Service
Responsável por: Validação, processamento e liquidação financeira.
"""
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timezone
from decimal import Decimal
import os
import logging

# Configuração básica
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'postgresql://agrokongo:senha_segura@db:5432/agrokongo_pagamentos'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'payment-service-dev-key')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- MODELOS ESPECÍFICOS DO SERVIÇO DE PAGAMENTOS ---
class TransacaoFinanceira(db.Model):
    """Espelho das transações para processamento financeiro."""
    __tablename__ = 'transacoes_financeiras'
    
    id = db.Column(db.Integer, primary_key=True)
    transacao_original_id = db.Column(db.Integer, nullable=False, index=True)  # ID da transação original
    fatura_ref = db.Column(db.String(50), unique=True, nullable=False)
    
    valor_total = db.Column(db.Numeric(14, 2), nullable=False)
    comissao = db.Column(db.Numeric(14, 2), default=0.00)
    valor_liquido = db.Column(db.Numeric(14, 2), default=0.00)
    
    status_pagamento = db.Column(db.String(30), default='pendente')
    metodo_pagamento = db.Column(db.String(50))
    
    comprovativo_path = db.Column(db.String(255))
    validado_por = db.Column(db.Integer)  # ID do admin que validou
    
    data_criacao = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    data_validacao = db.Column(db.DateTime(timezone=True))
    data_liquidacao = db.Column(db.DateTime(timezone=True))
    
    # Auditoria
    tentativas_validacao = db.Column(db.Integer, default=0)
    ultimo_erro = db.Column(db.Text)


class MovimentacaoFinanceira(db.Model):
    """Registra todas as movimentações financeiras (débito/crédito)."""
    __tablename__ = 'movimentacoes_financeiras'
    
    id = db.Column(db.Integer, primary_key=True)
    transacao_id = db.Column(db.Integer, db.ForeignKey('transacoes_financeiras.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'credito' ou 'debito'
    valor = db.Column(db.Numeric(14, 2), nullable=False)
    descricao = db.Column(db.String(255))
    conta_destino = db.Column(db.String(100))  # IBAN ou referência
    data_movimentacao = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    transacao = db.relationship('TransacaoFinanceira', backref='movimentacoes')


# --- API REST DO SERVIÇO DE PAGAMENTOS ---
@app.route('/health')
def health_check():
    """Health check do serviço."""
    return jsonify({
        'service': 'agrokongo-payment-service',
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@app.route('/api/v1/pagamentos/<int:transacao_id>', methods=['POST'])
def processar_pagamento(transacao_id):
    """
    Processa pagamento de uma transação.
    
    Payload esperado:
    {
        "valor": 2500.00,
        "metodo": "transferencia_bancaria",
        "comprovativo": "path/to/comprovativo.jpg"
    }
    """
    try:
        data = request.get_json()
        
        # Validar dados
        if not data or 'valor' not in data:
            return jsonify({'error': 'Valor é obrigatório'}), 400
        
        valor = Decimal(str(data['valor']))
        if valor <= 0:
            return jsonify({'error': 'Valor deve ser positivo'}), 400
        
        # Calcular comissão automaticamente (5%)
        comissao = valor * Decimal('0.05')
        valor_liquido = valor - comissao
        
        # Criar registo financeiro
        transacao = TransacaoFinanceira(
            transacao_original_id=transacao_id,
            fatura_ref=f"PAY-{datetime.now().year}-{transacao_id}",
            valor_total=valor,
            comissao=comissao.quantize(Decimal('0.01')),
            valor_liquido=valor_liquido.quantize(Decimal('0.01')),
            metodo_pagamento=data.get('metodo', 'transferencia_bancaria'),
            comprovativo_path=data.get('comprovativo')
        )
        
        db.session.add(transacao)
        db.session.commit()
        
        logger.info(f"Pagamento processado: Ref={transacao.fatura_ref}, Valor={valor}")
        
        return jsonify({
            'success': True,
            'transacao_id': transacao.id,
            'fatura_ref': transacao.fatura_ref,
            'valor_liquido': str(transacao.valor_liquido)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao processar pagamento: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/pagamentos/<int:id>/validar', methods=['POST'])
def validar_pagamento(id):
    """Valida pagamento pendente (admin)."""
    try:
        transacao = TransacaoFinanceira.query.get_or_404(id)
        
        if transacao.status_pagamento == 'validado':
            return jsonify({'error': 'Pagamento já validado'}), 400
        
        transacao.status_pagamento = 'validado'
        transacao.data_validacao = datetime.now(timezone.utc)
        transacao.validado_por = request.headers.get('X-Admin-ID')
        
        # Registar movimentação de crédito para o vendedor
        movimentacao = MovimentacaoFinanceira(
            transacao_id=transacao.id,
            tipo='credito',
            valor=transacao.valor_liquido,
            descricao=f"Liquidação venda {transacao.fatura_ref}",
            conta_destino="IBAN_VENDEDOR"  # Deveria vir do perfil do vendedor
        )
        
        db.session.add(movimentacao)
        db.session.commit()
        
        logger.info(f"Pagemento validado: Ref={transacao.fatura_ref}")
        
        return jsonify({
            'success': True,
            'message': 'Pagamento validado com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro na validação: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/pagamentos/<int:id>/liquidar', methods=['POST'])
def liquidar_pagamento(id):
    """Efetua liquidação final ao produtor."""
    try:
        transacao = TransacaoFinanceira.query.get_or_404(id)
        
        if transacao.status_pagamento != 'validado':
            return jsonify({'error': 'Pagamento precisa estar validado'}), 400
        
        if transacao.data_liquidacao:
            return jsonify({'error': 'Pagamento já liquidado'}), 400
        
        transacao.data_liquidacao = datetime.now(timezone.utc)
        
        # Registar movimentação de débito da plataforma
        movimentacao = MovimentacaoFinanceira(
            transacao_id=transacao.id,
            tipo='debito',
            valor=transacao.comissao,
            descricao=f"Comissão plataforma venda {transacao.fatura_ref}"
        )
        
        db.session.add(movimentacao)
        db.session.commit()
        
        logger.info(f"Pagemento liquidado: Ref={transacao.fatura_ref}")
        
        return jsonify({
            'success': True,
            'message': 'Liquidação efetuada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro na liquidação: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/pagamentos/relatorio-financeiro', methods=['GET'])
def relatorio_financeiro():
    """Gera relatório financeiro consolidado."""
    try:
        # Totais gerais
        total_transacoes = TransacaoFinanceira.query.count()
        total_validados = TransacaoFinanceira.query.filter_by(status_pagamento='validado').count()
        
        soma_valores = db.session.query(
            db.func.sum(TransacaoFinanceira.valor_total),
            db.func.sum(TransacaoFinanceira.comissao),
            db.func.sum(TransacaoFinanceira.valor_liquido)
        ).filter(
            TransacaoFinanceira.status_pagamento == 'validado'
        ).first()
        
        return jsonify({
            'resumo': {
                'total_transacoes': total_transacoes,
                'transacoes_validadas': total_validados,
                'volume_total': str(soma_valores[0] or 0),
                'comissoes_totais': str(soma_valores[1] or 0),
                'total_liquidado': str(soma_valores[2] or 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Erro no relatório: {e}")
        return jsonify({'error': str(e)}), 500


# --- INICIALIZAÇÃO ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
