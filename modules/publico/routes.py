from flask import Blueprint, render_template, flash, redirect, url_for
from core.models import Safra, Produto, Provincia, Usuario
from flask_login import current_user

# Definimos o Blueprint 'publico'
publico_bp = Blueprint('publico', __name__)

@publico_bp.route('/')
def home():
    """Página de Boas-vindas (Landing Page)."""
    # Mostra safras recentes para dar vida à página inicial
    safras_destaque = Safra.query.filter_by(status='disponivel')\
        .order_by(Safra.data_publicacao.desc()).limit(4).all()
    return render_template('home.html', safras=safras_destaque)

@publico_bp.route('/sobre')
def sobre():
    """Página institucional sobre a missão do AgroKongo em Angola."""
    return render_template('publico/sobre.html')

@publico_bp.route('/contacto')
@publico_bp.route('/suporte') # Unificado: dois caminhos para a mesma página
def contacto():
    """Unificamos suporte e contacto para evitar redundância."""
    return render_template('publico/contacto.html')

@publico_bp.route('/safra/<int:safra_id>')
def detalhes_safra(safra_id):
    """Página detalhada de uma safra, acessível por todos."""
    safra = Safra.query.get_or_404(safra_id)

    # Lógica de Sugestões: Mesma província ou mesmo produto
    relacionados = Safra.query.filter(
        Safra.produto_id == safra.produto_id,
        Safra.id != safra.id,
        Safra.status == 'disponivel'
    ).limit(3).all()

    return render_template('mercado/detalhes_safra.html',
                           safra=safra,
                           relacionados=relacionados)

@publico_bp.route('/produtor/<int:usuario_id>')
def perfil_produtor(usuario_id):
    """Visualização pública do perfil do produtor para compradores."""
    produtor = Usuario.query.get_or_404(usuario_id)

    if produtor.tipo != 'produtor':
        flash('Este perfil não pertence a um produtor.', 'info')
        # Tenta redirecionar para o mercado se existir, senão para a home
        try:
            return redirect(url_for('mercado.explorar'))
        except:
            return redirect(url_for('publico.home'))

    return render_template('perfil_publico.html', produtor=produtor)