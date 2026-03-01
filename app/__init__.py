import os
from flask import Flask, send_from_directory, render_template, abort
from flask_login import login_required, current_user
from flask_apscheduler import APScheduler
from datetime import datetime, timezone, timedelta
from app.extensions import db, setup_extensions
from app.models import Transacao, TransactionStatus
from config import config_dict

# Instância global do scheduler
scheduler = APScheduler()


def processar_monitorizacao_pagamentos(app):
    """Auditoria automática para evitar que transações fiquem 'esquecidas'."""
    with app.app_context():
        agora = datetime.now(timezone.utc)
        limite = agora - timedelta(hours=24)
        try:
            # Selecionamos apenas IDs e Refs para poupar memória na consulta
            estagnadas = Transacao.query.filter(
                Transacao.status == TransactionStatus.ANALISE,
                Transacao.data_criacao <= limite
            ).all()

            for t in estagnadas:
                app.logger.warning(f"AUDITORIA: Fatura {t.fatura_ref} em análise há mais de 24h.")
                # Aqui poderias disparar um e-mail automático para o Admin

        except Exception as e:
            app.logger.error(f"Erro no Scheduler: {e}")


def create_app(config_name='dev'):
    app = Flask(__name__)
    app.config.from_object(config_dict[config_name])
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

    setup_extensions(app)
    _registrar_context_processors(app)
    _registrar_rotas_arquivos(app)
    _criar_diretorios(app)
    _registrar_blueprints(app)
    _configurar_scheduler(app)
    _registrar_error_handlers(app)

    return app


def _registrar_context_processors(app):
    """Registra processadores de contexto global."""
    @app.context_processor
    def inject_globals():
        return {
            'agora': datetime.now(timezone.utc),
            'TStatus': TransactionStatus,
            'now': datetime.now(),
            'timedelta': timedelta
        }


def _registrar_rotas_arquivos(app):
    """Registra rotas para servir arquivos públicos e privados."""
    @app.route('/uploads/safras/<filename>')
    def serve_safra_image(filename):
        folder = os.path.join(app.config['UPLOAD_FOLDER_PUBLIC'], 'safras')
        return send_from_directory(folder, filename)

    @app.route('/uploads/comprovativos/<filename>')
    @login_required
    def serve_comprovativo(filename):
        from flask import current_app
        transacao = Transacao.query.filter_by(comprovativo_path=filename).first_or_404()

        pode_ver = [
            current_user.tipo == 'admin',
            current_user.id == transacao.comprador_id,
            current_user.id == transacao.vendedor_id
        ]

        if not any(pode_ver):
            current_app.logger.warning(f"TENTATIVA DE INTRUSÃO: User {current_user.id} tentou ver talão {filename}")
            abort(403)

        private_folder = os.path.join(current_app.config['UPLOAD_FOLDER_PRIVATE'], 'comprovativos')
        return send_from_directory(directory=private_folder, path=filename, mimetype='image/jpeg')


def _criar_diretorios(app):
    """Cria diretórios necessários se não existirem."""
    with app.app_context():
        pastas = [
            os.path.join(app.config['UPLOAD_FOLDER_PUBLIC'], 'safras'),
            os.path.join(app.config['UPLOAD_FOLDER_PUBLIC'], 'perfil'),
            os.path.join(app.config['UPLOAD_FOLDER_PRIVATE'], 'comprovativos'),
            os.path.join(app.config['UPLOAD_FOLDER_PRIVATE'], 'documentos')
        ]
        for pasta in pastas:
            os.makedirs(pasta, exist_ok=True)


def _registrar_blueprints(app):
    """Registra todos os blueprints da aplicação."""
    from app.routes.auth import auth_bp
    from app.routes.produtor import produtor_bp
    from app.routes.main import main_bp
    from app.routes.mercado import mercado_bp
    from app.routes.admin import admin_bp
    from app.routes.comprador import comprador_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(mercado_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(comprador_bp, url_prefix='/comprador')
    app.register_blueprint(produtor_bp, url_prefix='/produtor')


def _configurar_scheduler(app):
    """Configura e inicia o scheduler de tarefas."""
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        if not scheduler.running:
            scheduler.init_app(app)
            scheduler.add_job(
                id='audit_pagamentos',
                func=processar_monitorizacao_pagamentos,
                args=[app],
                trigger='interval',
                hours=1
            )
            scheduler.start()


def _registrar_error_handlers(app):
    """Registra handlers de erro."""
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500