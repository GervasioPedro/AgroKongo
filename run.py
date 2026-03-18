import os
from dotenv import load_dotenv

# 1. Prioridade Máxima: Carregar segredos e variáveis de ambiente
load_dotenv()

# 2. Definição de Ambiente com Fallback Seguro
env_config = os.environ.get('FLASK_ENV', 'development')

from app import create_app, db

# 3. Inicialização da Aplicação Factory
app = create_app(env_config)

# 4. Hook de Inicialização (Útil para logs de arranque)
with app.app_context():
    # Log de verificação (visível nos logs do servidor)
    print(f"🚀 AgroKongo em modo: {env_config.upper()}")
    # Se quiseres auto-criar as tabelas em ambientes simples (como Render):
    # db.create_all()

if __name__ == "__main__":
    # Apenas para desenvolvimento local
    app.run(host='0.0.0.0', port=5000, debug=(env_config == 'development'))