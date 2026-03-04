from flask import Blueprint, redirect

# Blueprint para redirecionar rotas HTML legadas para o SPA (Next.js)
legacy_redirects_bp = Blueprint('legacy_redirects', __name__)

# Mapa de rotas legadas -> rotas SPA correspondentes
_REDIRECTS = {
    # Cadastro de produtor (fluxo legado HTML) → fluxo SPA
    '/criar-conta-produtor': '/auth/cadastro/passo-1',
    '/validar-otp': '/auth/cadastro/passo-2',
    '/dados-basicos': '/auth/cadastro/passo-3',
    '/definir-senha': '/auth/cadastro/passo-3',
    '/dados-financeiros': '/auth/cadastro/passo-3',
    # Reenvio de OTP (HTML) → passo 2 do SPA (a ação real deve ser via /api/cadastro/reenviar-otp)
    '/reenviar-otp': '/auth/cadastro/passo-2',
}

# Registrar rotas GET e POST para cada caminho legado
for old_path, new_path in _REDIRECTS.items():
    # GET
    legacy_redirects_bp.add_url_rule(
        old_path,
        endpoint=f"redir_get_{old_path.strip('/').replace('-', '_') or 'root'}",
        view_func=lambda new_path=new_path: redirect(new_path, code=302),
        methods=['GET']
    )
    # POST
    legacy_redirects_bp.add_url_rule(
        old_path,
        endpoint=f"redir_post_{old_path.strip('/').replace('-', '_') or 'root'}",
        view_func=lambda new_path=new_path: redirect(new_path, code=302),
        methods=['POST']
    )
