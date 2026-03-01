"""
Health Check Endpoint para Monitorização
"""
from flask import Blueprint, jsonify
from app.extensions import db
import redis
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificar saúde da aplicação
    Usado por Render, Railway, etc para monitorização
    """
    status = {
        'status': 'healthy',
        'database': 'unknown',
        'redis': 'unknown'
    }
    
    # Verificar conexão com base de dados
    try:
        db.session.execute('SELECT 1')
        status['database'] = 'connected'
    except Exception as e:
        status['database'] = f'error: {str(e)}'
        status['status'] = 'unhealthy'
    
    # Verificar conexão com Redis (se configurado)
    redis_url = os.environ.get('REDIS_URL')
    if redis_url:
        try:
            r = redis.from_url(redis_url)
            r.ping()
            status['redis'] = 'connected'
        except Exception as e:
            status['redis'] = f'error: {str(e)}'
            status['status'] = 'degraded'
    else:
        status['redis'] = 'not_configured'
    
    http_status = 200 if status['status'] == 'healthy' else 503
    return jsonify(status), http_status

@health_bp.route('/ping', methods=['GET'])
def ping():
    """Endpoint simples para verificar se a aplicação está a responder"""
    return jsonify({'message': 'pong'}), 200
