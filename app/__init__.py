import os
from flask import Flask, send_from_directory, render_template, abort
from flask_cors import CORS
from flask_login import login_required, current_user
from flask_apscheduler import APScheduler
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from datetime import datetime, timezone, timedelta
from app.extensions import db, setup_extensions
from app.models import Transacao, TransactionStatus
from config import config_dict

# Instância global do scheduler
scheduler = APScheduler()

# Configuração do Rate Limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379/0",
    strategy="fixed-window"
)


def processar_monitorizacao_pagamentos(app):
    """Auditoria automática para evitar que transações fiquem 'esquecidas'."""
    with app.app_context():
        agora = datetime.now(timezone.utc)
        limite = agora - timedelta(hours=24)
        try:
            # Selecionamos apenas IDs e Refs para poupar memória na consulta
            estagnadas = Transacao.query.filter(
                Transacao.status == TransactionStatus.ANALISE.value,
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

    # Configurar CORS para permitir requisições do frontend Next.js
    # Abrange tanto as rotas de API quanto as de autenticação
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        },
        r"/auth/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
            "supports_credentials": True
        }
    })

    # Configuração JWT
    app.config["JWT_SECRET_KEY"] = app.config.get('SECRET_KEY', 'agro-kongo-jwt-secret')  # Fallback seguro
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    jwt = JWTManager(app)

    # 1. Segurança de Uploads: Limite de 5MB por ficheiro (Essencial em Produção)
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

    # Inicializa Rate Limiter com Redis (ou memory fallback)
    limiter.init_app(app)

    setup_extensions(app)

    @app.context_processor
    def inject_globals():
        return {
            'agora': datetime.now(timezone.utc),
            'TStatus': TransactionStatus,
            'now': datetime.now(),
            'timedelta': timedelta
        }

    # 2. SERVIÇO DE FICHEIROS COM PROTEÇÃO DE PRIVACIDADE
    @app.route('/uploads/safras/<filename>')
    def serve_safra_image(filename):
        folder = os.path.join(app.config['UPLOAD_FOLDER_PUBLIC'], 'safras')
        return send_from_directory(folder, filename)

    @app.route('/uploads/comprovativos/<filename>')
    @login_required
    def serve_comprovativo(filename):
        """Serve talões bancários apenas para partes interessadas (Admin, Comprador, Vendedor)."""

        # 1. Localizar a transação na DB
        transacao = Transacao.query.filter_by(comprovativo_path=filename).first_or_404()

        # 2. Verificar permissões (Lógica de Escrow)
        pode_ver = [
            current_user.tipo == 'admin',
            current_user.id == transacao.comprador_id,
            current_user.id == transacao.vendedor_id
        ]

        if not any(pode_ver):
            current_app.logger.warning(f"TENTATIVA DE INTRUSÃO: User {current_user.id} tentou ver talão {filename}")
            abort(403)

        # 3. Definir o caminho absoluto para evitar erros no Windows
        private_folder = os.path.join(current_app.config['UPLOAD_FOLDER_PRIVATE'], 'comprovativos')

        # 4. Enviar ficheiro com proteção contra Directory Traversal
        return send_from_directory(
            directory=private_folder,
            path=filename,
            mimetype='image/jpeg'
        )

    # 3. GESTÃO DE DIRETÓRIOS (Auto-healing)
    with app.app_context():
        pastas = [
            os.path.join(app.config['UPLOAD_FOLDER_PUBLIC'], 'safras'),
            os.path.join(app.config['UPLOAD_FOLDER_PUBLIC'], 'perfil'),
            os.path.join(app.config['UPLOAD_FOLDER_PRIVATE'], 'comprovativos'),
            os.path.join(app.config['UPLOAD_FOLDER_PRIVATE'], 'documentos')
        ]
        for pasta in pastas:
            if not os.path.exists(pasta):
                os.makedirs(pasta, exist_ok=True)

    # 4. BLUEPRINTS - MODULARIZADOS
    from app.routes.auth import auth_bp, auth_api_bp
    from app.routes.produtor import produtor_bp
    from app.routes.main import main_bp
    from app.routes.mercado import mercado_bp
    from app.routes.mercado_api import mercado_api_bp
    from app.routes.utils_api import utils_api_bp
    from app.routes.dashboard_api import dashboard_api_bp # <-- NOVO
    from app.routes.comprador import comprador_bp
    from app.routes.chat import chat_bp
    from app.routes.api import api_bp
    from app.routes.swagger import swagger_bp
    
    # Admin modularizado (dividido por responsabilidades)
    from app.routes.admin import admin_bp
    from app.routes.admin_dashboard import admin_dashboard_bp
    from app.routes.admin_pagamentos import admin_pagamentos_bp
    from app.routes.admin_disputas import admin_disputas_bp
    from app.routes.admin_usuarios import admin_usuarios_bp
    from app.routes.admin_relatorios import admin_relatorios_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(mercado_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth') 
    app.register_blueprint(auth_api_bp, url_prefix='/api/auth')
    app.register_blueprint(mercado_api_bp, url_prefix='/api/market')
    app.register_blueprint(utils_api_bp, url_prefix='/api/utils')
    app.register_blueprint(dashboard_api_bp, url_prefix='/api/dashboard') # <-- NOVO

    app.register_blueprint(comprador_bp, url_prefix='/comprador')
    app.register_blueprint(produtor_bp, url_prefix='/produtor')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(api_bp)
    app.register_blueprint(swagger_bp)
    
    # Registro dos blueprints do Admin com prefixo único
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(admin_dashboard_bp, url_prefix='/admin')
    app.register_blueprint(admin_pagamentos_bp, url_prefix='/admin')
    app.register_blueprint(admin_disputas_bp, url_prefix='/admin')
    app.register_blueprint(admin_usuarios_bp, url_prefix='/admin')
    app.register_blueprint(admin_relatorios_bp, url_prefix='/admin')

    # 5. SCHEDULER DE TAREFAS
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        if not scheduler.running:
            scheduler.init_app(app)
            misfire_grace_time = 300 if app.debug else 60
            scheduler.add_job(id='audit_pagamentos', func=processar_monitorizacao_pagamentos,
                              args=[app], trigger='interval', hours=1,
                              misfire_grace_time=misfire_grace_time)
            scheduler.start()

    # 6. HANDLERS DE ERRO
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app