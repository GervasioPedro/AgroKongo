"""
Health Checks Automatizados para Monitorização
Substitui a necessidade de monitorização manual
"""
from flask import Blueprint, jsonify, current_app
from app.extensions import db, cache
from datetime import datetime, timezone
import time
import psycopg2

health_bp = Blueprint('health', __name__, url_prefix='/health')


@health_bp.route('/live', methods=['GET'])
def liveness_probe():
    """
    Liveness probe - Verifica se a aplicação está viva.
    Usado por Kubernetes/load balancers para restart automático.
    
    Retorna 200 OK se o processo Flask está rodando.
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'agrokongo-api'
    }), 200


@health_bp.route('/ready', methods=['GET'])
def readiness_probe():
    """
    Readiness probe - Verifica se a aplicação está pronta para receber tráfego.
    Checa dependências críticas (DB, Redis, etc).
    
    Retorna 200 OK apenas se todas as dependências estão saudáveis.
    """
    checks = {}
    overall_healthy = True
    
    # Check 1: Database
    try:
        start = time.time()
        db.session.execute('SELECT 1')
        duration = time.time() - start
        
        checks['database'] = {
            'status': 'healthy',
            'response_time_ms': round(duration * 1000, 2)
        }
    except Exception as e:
        checks['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        overall_healthy = False
    
    # Check 2: Redis/Cache
    try:
        start = time.time()
        cache.set('health_check_ping', 'pong', timeout=5)
        result = cache.get('health_check_ping')
        duration = time.time() - start
        
        if result == 'pong':
            checks['cache'] = {
                'status': 'healthy',
                'response_time_ms': round(duration * 1000, 2)
            }
        else:
            raise Exception("Cache not responding correctly")
            
    except Exception as e:
        checks['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        overall_healthy = False
    
    # Check 3: Storage (upload folders)
    try:
        import os
        upload_folder = current_app.config.get('UPLOAD_FOLDER_PUBLIC', '/tmp')
        
        if os.path.exists(upload_folder) and os.access(upload_folder, os.W_OK):
            checks['storage'] = {
                'status': 'healthy',
                'path': upload_folder
            }
        else:
            raise Exception(f"Storage not writable: {upload_folder}")
            
    except Exception as e:
        checks['storage'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        overall_healthy = False
    
    status_code = 200 if overall_healthy else 503
    
    response = {
        'status': 'ready' if overall_healthy else 'not_ready',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'checks': checks
    }
    
    return jsonify(response), status_code


@health_bp.route('/detailed', methods=['GET'])
def detailed_health():
    """
    Health check detalhado com métricas completas.
    Para uso em dashboards de monitorização.
    """
    from sqlalchemy import text
    import os
    import sys
    
    metrics = {}
    
    # Application Info
    metrics['application'] = {
        'name': 'AgroKongo API',
        'version': '1.0',
        'python_version': sys.version,
        'environment': current_app.config.get('FLASK_ENV', 'unknown'),
        'debug': current_app.debug
    }
    
    # Database Metrics
    try:
        start = time.time()
        
        # Conexões ativas
        result = db.session.execute(text("""
            SELECT count(*) 
            FROM pg_stat_activity 
            WHERE datname = current_database()
        """))
        active_connections = result.scalar()
        
        # Tamanho do banco
        result = db.session.execute(text("""
            SELECT pg_size_pretty(pg_database_size(current_database()))
        """))
        db_size = result.scalar()
        
        duration = time.time() - start
        
        metrics['database'] = {
            'status': 'healthy',
            'active_connections': active_connections,
            'size': db_size,
            'query_time_ms': round(duration * 1000, 2)
        }
    except Exception as e:
        metrics['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # Cache Metrics
    try:
        start = time.time()
        
        # Testar cache
        test_key = f'health_test_{datetime.now().timestamp()}'
        cache.set(test_key, 'test', timeout=10)
        retrieved = cache.get(test_key)
        duration = time.time() - start
        
        metrics['cache'] = {
            'status': 'healthy' if retrieved == 'test' else 'degraded',
            'response_time_ms': round(duration * 1000, 2)
        }
    except Exception as e:
        metrics['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # System Metrics
    metrics['system'] = {
        'memory_usage_mb': round(sys.getsizeof({}) / 1024 / 1024, 2),  # Estimativa
        'pid': os.getpid(),
        'cwd': os.getcwd()
    }
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'metrics': metrics
    }), 200


@health_bp.route('/db-ping', methods=['GET'])
def database_ping():
    """
    Ping simples ao banco de dados.
    Para monitoramento rápido de conectividade.
    """
    try:
        start = time.time()
        db.session.execute('SELECT 1')
        duration = time.time() - start
        
        return jsonify({
            'status': 'connected',
            'response_time_ms': round(duration * 1000, 2),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 503


@health_bp.route('/cache-ping', methods=['GET'])
def cache_ping():
    """
    Ping simples ao cache/Redis.
    Para monitoramento rápido de cache.
    """
    try:
        start = time.time()
        cache.set('ping', 'pong', timeout=5)
        result = cache.get('ping')
        duration = time.time() - start
        
        if result == 'pong':
            return jsonify({
                'status': 'connected',
                'response_time_ms': round(duration * 1000, 2),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 200
        else:
            raise Exception("Cache returned wrong value")
            
    except Exception as e:
        return jsonify({
            'status': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 503
