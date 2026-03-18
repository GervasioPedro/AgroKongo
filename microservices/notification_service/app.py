"""
Microsserviço de Notificações - AgroKongo Notification Service
Responsável por: Email, SMS, Push Notifications e notificações in-app.
"""
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timezone
import os
import logging
import json
from typing import Dict, List

# Configuração básica
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://agrokongo:senha_segura@db:5432/agrokongo_notificacoes'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'notification-service-dev-key')

# Configurações de serviços externos
app.config['EMAIL_HOST'] = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
app.config['EMAIL_PORT'] = int(os.environ.get('EMAIL_PORT', 587))
app.config['EMAIL_USER'] = os.environ.get('EMAIL_USER')
app.config['EMAIL_PASSWORD'] = os.environ.get('EMAIL_PASSWORD')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- MODELOS DO SERVIÇO DE NOTIFICAÇÕES ---
class Notificacao(db.Model):
    """Notificações in-app."""
    __tablename__ = 'notificacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False, index=True)
    titulo = db.Column(db.String(100))
    mensagem = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(50), default='info')  # info, warning, error, success
    link = db.Column(db.String(255))
    lida = db.Column(db.Boolean, default=False, index=True)
    data_criacao = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    data_leitura = db.Column(db.DateTime(timezone=True))


class TemplateEmail(db.Model):
    """Templates de email reutilizáveis."""
    __tablename__ = 'templates_email'
    
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True, nullable=False)  # ex: 'boas_vindas'
    assunto = db.Column(db.String(200), nullable=False)
    corpo_html = db.Column(db.Text, nullable=False)
    corpo_texto = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    data_atualizacao = db.Column(db.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))


class HistoricoEnvio(db.Model):
    """Histórico de todos os envios de notificações."""
    __tablename__ = 'historico_envios'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, index=True)
    tipo = db.Column(db.String(50), nullable=False)  # email, sms, push, in_app
    destinatario = db.Column(db.String(255), nullable=False)
    assunto = db.Column(db.String(200))
    conteudo = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pendente')  # pendente, enviado, falha
    erro = db.Column(db.Text)
    data_envio = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    data_entrega = db.Column(db.DateTime(timezone=True))


# --- API REST DO SERVIÇO DE NOTIFICAÇÕES ---
@app.route('/health')
def health_check():
    """Health check do serviço."""
    return jsonify({
        'service': 'agrokongo-notification-service',
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@app.route('/api/v1/notificacoes/criar', methods=['POST'])
def criar_notificacao():
    """
    Cria notificação in-app.
    
    Payload:
    {
        "usuario_id": 123,
        "titulo": "Nova compra!",
        "mensagem": "Sua safra foi comprada",
        "tipo": "success",
        "link": "/vendas/456"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'usuario_id' not in data or 'mensagem' not in data:
            return jsonify({'error': 'usuario_id e mensagem são obrigatórios'}), 400
        
        notificacao = Notificacao(
            usuario_id=data['usuario_id'],
            titulo=data.get('titulo'),
            mensagem=data['mensagem'],
            tipo=data.get('tipo', 'info'),
            link=data.get('link')
        )
        
        db.session.add(notificacao)
        db.session.commit()
        
        logger.info(f"Notificação criada para usuário {data['usuario_id']}")
        
        # Disparar envio assíncrono em background
        # processar_notificacao_async(notificacao.id)
        
        return jsonify({
            'success': True,
            'notificacao_id': notificacao.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar notificação: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/notificacoes/<int:usuario_id>/nao-lidas', methods=['GET'])
def listar_nao_lidas(usuario_id):
    """Lista notificações não lidas de um usuário."""
    try:
        notificacoes = Notificacao.query.filter_by(
            usuario_id=usuario_id,
            lida=False
        ).order_by(Notificacao.data_criacao.desc()).limit(50).all()
        
        return jsonify({
            'count': len(notificacoes),
            'notificacoes': [{
                'id': n.id,
                'titulo': n.titulo,
                'mensagem': n.mensagem,
                'tipo': n.tipo,
                'link': n.link,
                'data': n.data_criacao.isoformat()
            } for n in notificacoes]
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar notificações: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/notificacoes/marcar-lida/<int:id>', methods=['POST'])
def marcar_lida(id):
    """Marca notificação como lida."""
    try:
        notificacao = Notificacao.query.get_or_404(id)
        notificacao.lida = True
        notificacao.data_leitura = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao marcar como lida: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/email/enviar', methods=['POST'])
def enviar_email():
    """
    Envia email transacional.
    
    Payload:
    {
        "destinatario": "user@example.com",
        "template": "boas_vindas",
        "dados": {"nome": "João"},
        "assunto_personalizado": "Bem-vindo!"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'destinatario' not in data:
            return jsonify({'error': 'destinatário é obrigatório'}), 400
        
        # Carregar template se especificado
        template_chave = data.get('template')
        assunto = data.get('assunto_personalizado')
        corpo = data.get('corpo')
        
        if template_chave:
            template = TemplateEmail.query.filter_by(chave=template_chave, ativo=True).first()
            if not template:
                return jsonify({'error': f'Template {template_chave} não encontrado'}), 404
            
            assunto = assunto or template.assunto
            corpo = corpo or template.corpo_html
            
            # Substituir variáveis no template
            dados = data.get('dados', {})
            for chave, valor in dados.items():
                corpo = corpo.replace(f'{{{{{chave}}}}}', str(valor))
        
        # Registar histórico
        historico = HistoricoEnvio(
            usuario_id=data.get('usuario_id'),
            tipo='email',
            destinatario=data['destinatario'],
            assunto=assunto,
            conteudo=corpo,
            status='enviado'  # Em produção, seria processado async
        )
        
        db.session.add(historico)
        db.session.commit()
        
        # TODO: Integrar com Flask-Mail ou SendGrid
        # enviar_email_real(destinatario, assunto, corpo)
        
        logger.info(f"Email enviado para {data['destinatario']}")
        
        return jsonify({
            'success': True,
            'historico_id': historico.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao enviar email: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/notificacoes/broadcast', methods=['POST'])
def broadcast():
    """
    Envia notificação em massa para múltiplos usuários.
    
    Payload:
    {
        "usuarios_ids": [1, 2, 3],
        "mensagem": "Manutenção agendada",
        "tipo": "warning"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'usuarios_ids' not in data or 'mensagem' not in data:
            return jsonify({'error': 'usuarios_ids e mensagem são obrigatórios'}), 400
        
        usuarios_ids = data['usuarios_ids']
        notificacoes = []
        
        for usuario_id in usuarios_ids:
            notificacao = Notificacao(
                usuario_id=usuario_id,
                mensagem=data['mensagem'],
                tipo=data.get('tipo', 'info'),
                link=data.get('link')
            )
            notificacoes.append(notificacao)
        
        db.session.bulk_save_objects(notificacoes)
        db.session.commit()
        
        logger.info(f"Broadcast enviado para {len(usuarios_ids)} usuários")
        
        return jsonify({
            'success': True,
            'enviados': len(usuarios_ids)
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro no broadcast: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/templates/email', methods=['POST'])
def criar_template():
    """Cria ou atualiza template de email."""
    try:
        data = request.get_json()
        
        template = TemplateEmail(
            chave=data['chave'],
            assunto=data['assunto'],
            corpo_html=data['corpo_html'],
            corpo_texto=data.get('corpo_texto', '')
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({'success': True, 'template_id': template.id}), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar template: {e}")
        return jsonify({'error': str(e)}), 500


# --- INICIALIZAÇÃO ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Criar templates padrão se não existirem
        templates_padrao = [
            {
                'chave': 'boas_vindas',
                'assunto': 'Bem-vindo ao AgroKongo!',
                'corpo_html': '<h1>Olá {{nome}}!</h1><p>Bem-vindo à nossa plataforma.</p>'
            },
            {
                'chave': 'compra_realizada',
                'assunto': 'Compra realizada com sucesso',
                'corpo_html': '<p>Sua compra de {{produto}} foi confirmada!</p>'
            }
        ]
        
        for tpl in templates_padrao:
            existente = TemplateEmail.query.filter_by(chave=tpl['chave']).first()
            if not existente:
                db.session.add(TemplateEmail(**tpl))
        
        db.session.commit()
    
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=False)
