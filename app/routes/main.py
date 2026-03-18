import os
import hashlib
import base64
import io
import qrcode
import pdfkit
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app, abort,send_from_directory,make_response
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models import (
    Safra, Produto, Notificacao, Provincia,
    Municipio, Avaliacao, Usuario, Transacao, TransactionStatus
)
from app.utils.helpers import salvar_ficheiro
# Exemplo usando pdfkit ou weasyprint (ajusta conforme a tua biblioteca)
import pdfkit


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Vitrine: Otimizada para carregar produtos e imagens rapidamente."""
    safras_recentes = Safra.query.filter_by(status='disponivel') \
        .order_by(Safra.id.desc()).limit(4).all()
    return render_template('index.html', safras=safras_recentes)


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Encaminha o utilizador com base no tipo e estado de validação."""
    if not current_user.perfil_completo:
        flash("ℹ️ Quase lá! Complete o seu perfil para começar a negociar.", "info")
        return redirect(url_for('main.completar_perfil'))

    # Redirecionamento baseado em Role
    redirecionamentos = {
        'admin': 'admin_dashboard.dashboard',
        'produtor': 'produtor.dashboard',
        'comprador': 'comprador.dashboard'
    }

    endpoint = redirecionamentos.get(current_user.tipo, 'main.index')
    return redirect(url_for(endpoint))


@main_bp.route('/completar-perfil', methods=['GET', 'POST'])
@login_required
def completar_perfil():
    """Processo de KYC com gestão de ficheiros privados (BI/IBAN)."""
    # Permitimos acesso se o perfil estiver incompleto OU se o Admin marcou para revisão
    if current_user.perfil_completo and not request.args.get('editar'):
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        try:
            current_user.provincia_id = request.form.get('provincia_id')
            current_user.municipio_id = request.form.get('municipio_id')
            current_user.nif = request.form.get('nif', '').strip().upper()

            if current_user.tipo == 'produtor':
                # Normalização de IBAN Angolano
                current_user.iban = request.form.get('iban', '').replace(" ", "").upper()

            # Uploads: Um privado (Documentos) e um público (Foto)
            doc_file = request.files.get('documento')
            if doc_file and doc_file.filename != '':
                current_user.documento_pdf = salvar_ficheiro(doc_file, subpasta='identidade', privado=True)

            foto_file = request.files.get('foto')
            if foto_file and foto_file.filename != '':
                current_user.foto_perfil = salvar_ficheiro(foto_file, subpasta='perfil', privado=False)

            if current_user.verificar_e_atualizar_perfil():
                db.session.commit()
                flash('✅ Dados submetidos! A nossa equipa irá validar os seus documentos.', 'success')
                return redirect(url_for('main.dashboard'))

            flash('⚠️ Por favor, preencha todos os campos e anexe os documentos necessários.', 'warning')

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"ERRO_KYC_ID_{current_user.id}: {e}")
            flash('Houve um erro ao processar os seus dados. Tente novamente.', 'danger')

    provincias = Provincia.query.order_by(Provincia.nome).all()
    return render_template('main/completar_perfil.html', provincias=provincias)


@main_bp.route('/ler-notificacao/<int:id>')
@login_required
def ler_notificacao(id):
    """Gere a leitura de notificações e redirecionamento seguro."""
    notif = Notificacao.query.get_or_404(id)

    # Segurança: Impedir que um utilizador leia notificações de outro
    if notif.usuario_id != current_user.id:
        abort(403)

    notif.lida = True
    db.session.commit()

    # Redireciona para o link da notificação ou para o dashboard por defeito
    destino = notif.link if notif.link else url_for('main.dashboard')
    return redirect(destino)


@main_bp.route('/api/municipios/<int:provincia_id>')
def get_municipios(provincia_id):
    """Dropdown dinâmico para os municípios de Angola."""
    municipios = Municipio.query.filter_by(provincia_id=provincia_id).order_by(Municipio.nome).all()
    return jsonify([{'id': m.id, 'nome': m.nome} for m in municipios])


@main_bp.route('/perfil')
@login_required
def perfil():
    """Vista de resumo do utilizador com KPIs rápidos."""
    usuario = current_user
    estatisticas = {}

    if usuario.tipo == 'admin':
        # Receita da plataforma (5% de cada venda finalizada)
        receita = db.session.query(
            func.sum(Transacao.comissao_plataforma)
        ).filter(Transacao.status == TransactionStatus.FINALIZADO).scalar() or Decimal('0.00')

        estatisticas['receita'] = receita
        estatisticas['usuarios'] = Usuario.query.count()
        estatisticas['alertas'] = Transacao.query.filter_by(status=TransactionStatus.ANALISE).count()

    return render_template('auth/perfil.html', usuario=usuario, stats=estatisticas)

@main_bp.route('/limpar-notificacoes', methods=['POST'])
@login_required
def limpar_notificacoes():
    """
    Versão com redirecionamento (caso use um botão físico 'Marcar todas como lidas').
    """
    Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).update({Notificacao.lida: True})
    db.session.commit()
    return redirect(request.referrer or url_for('main.index'))

@main_bp.route('/marcar-lidas', methods=['POST'])
@login_required
def marcar_notificacoes_lidas():
    """Limpa o contador via AJAX quando o utilizador abre o menu do sininho."""
    Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).update({'lida': True})
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Notificações marcadas como lidas'})


@main_bp.route('/produtor/<int:id>')
def perfil_produtor(id):
    produtor = Usuario.query.get_or_404(id)
    avaliacoes = Avaliacao.query.filter_by(produtor_id=id).order_by(Avaliacao.data_criacao.desc()).all()

    # Cálculo da média usando SQLAlchemy func
    media = db.session.query(func.avg(Avaliacao.estrelas)).filter(Avaliacao.produtor_id == id).scalar() or 0

    return render_template('main/perfil_produtor.html',
                           produtor=produtor,
                           avaliacoes=avaliacoes,
                           media=round(media, 1))


@main_bp.route('/media/publico/<subpasta>/<filename>')
def servir_publico(subpasta, filename):
    base_dir = os.path.abspath(current_app.config['UPLOAD_FOLDER_PUBLIC'])
    diretorio = os.path.join(base_dir, subpasta)

    print(f"DEBUG: A tentar ler ficheiro público em: {os.path.join(diretorio, filename)}")

    return send_from_directory(diretorio, filename)

# Rota para Fotos de Perfil (Públicas)
@main_bp.route('/uploads/perfil/<filename>')
def serve_perfil(filename):
    # Aponta para data_storage/public/perfil
    folder = os.path.join(current_app.config['UPLOAD_FOLDER_PUBLIC'], 'perfil')
    
    # Se o arquivo não existir, serve imagem placeholder do static/img
    if not os.path.exists(os.path.join(folder, filename)):
        # Tenta servir do diretório de uploads primeiro
        default_folder = os.path.join(current_app.static_folder, 'img')
        return send_from_directory(default_folder, 'default_user.svg', mimetype='image/svg+xml')
    
    return send_from_directory(folder, filename)


# Rota para Imagens de Safras (Públicas)
@main_bp.route('/uploads/safras/<filename>')
def serve_safra_image(filename):
    """
    Serve imagens das safras dos produtores.
    Se a imagem não existir, retorna placeholder.
    """
    # Aponta para data_storage/public/safras
    folder = os.path.join(current_app.config['UPLOAD_FOLDER_PUBLIC'], 'safras')
    
    # Se o arquivo não existir, serve imagem placeholder
    if not os.path.exists(os.path.join(folder, filename)):
        # Retorna URL de placeholder externo
        return redirect('https://dummyimage.com/800x600/e2e8f0/16a34a&text=Sem+Imagem')
    
    return send_from_directory(folder, filename)


@main_bp.route('/media/privado/<subpasta>/<filename>')
@login_required
def servir_privado(subpasta, filename):
    """
    Serve arquivos privados (comprovativos, documentos) com autenticação.
    Apenas usuários logados podem acessar estes arquivos.
    """
    # Mapeamento de subpastas permitidas
    pastas_validas = {
        'comprovativos': 'comprovativos',
        'documentos': 'documentos'
    }
    
    if subpasta not in pastas_validas:
        abort(403)  # Subpasta não permitida
    
    # Caminho base: .../agrokongoVS/data_storage/private/<subpasta>
    directory = os.path.join(current_app.config['UPLOAD_FOLDER_PRIVATE'], subpasta)
    
    # Debug para verificação no terminal
    print(f"DEBUG: A tentar ler ficheiro privado em: {os.path.join(directory, filename)}")
    
    try:
        return send_from_directory(directory, filename)
    except FileNotFoundError:
        print(f"ERRO: Arquivo não encontrado: {filename}")
        abort(404)


@main_bp.route('/health')
def health_check():
    """
    Endpoint para health checks do Docker e load balancers.
    Verifica saúde da aplicação e dependências críticas.
    """
    from app.extensions import db
    from datetime import datetime, timezone
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0',
        'checks': {}
    }
    
    # Check 1: Database
    try:
        db.session.execute('SELECT 1')
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check 2: Redis (se configurado)
    try:
        redis_url = current_app.config.get('REDIS_URL')
        if redis_url:
            from app.extensions import celery, CELERY_AVAILABLE
            if CELERY_AVAILABLE and celery is not None:
                inspect = celery.control.inspect()
                active_queues = inspect.active_queues()
                if active_queues:
                    health_status['checks']['redis'] = 'ok'
                else:
                    health_status['checks']['redis'] = 'warning: no active workers'
            else:
                health_status['checks']['redis'] = 'not available (Celery disabled)'
        else:
            health_status['checks']['redis'] = 'not configured'
    except Exception as e:
        health_status['checks']['redis'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'
    
    # Return status code based on health
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return jsonify(health_status), status_code



@main_bp.route('/servir-documento/<filename>')
@login_required
def servir_documento(filename):
    # O caminho base: .../agrokongoVS/data_storage/private/documentos
    directory = os.path.join(current_app.config['UPLOAD_FOLDER_PRIVATE'], 'documentos')

    # Debug para veres no terminal se o caminho está correto
    print(f"A procurar PDF em: {directory}/{filename}")

    try:
        return send_from_directory(directory, filename)
    except FileNotFoundError:
        abort(404)


@main_bp.route('/fatura/visualizar/<int:trans_id>')
@login_required
def visualizar_fatura(trans_id):
    venda = Transacao.query.get_or_404(trans_id)
    # Verifica se o user faz parte da transação
    return render_template('documentos/fatura_geral.html', venda=venda)




@main_bp.route('/gerar_fatura/<int:trans_id>')
@login_required
def baixar_fatura(trans_id):
    # 1. Buscar a transação ou erro 404
    venda = Transacao.query.get_or_404(trans_id)

    # 2. Segurança: Apenas comprador, vendedor ou admin podem aceder
    # Ajustado para checar role corretamente
    is_admin = getattr(current_user, 'role', None) == 'admin'
    if current_user.id not in [venda.vendedor_id, venda.comprador_id] and not is_admin:
        abort(403)

    # 3. Gerar Hash de Verificação Único (SHA-256)
    hash_seed = f"{venda.id}-{venda.data_criacao}-{venda.valor_total_pago}"
    verificacao_hash = hashlib.sha256(hash_seed.encode()).hexdigest()[:16].upper()

    # 4. Gerar QR Code em Base64 para o template
    qr_data = f"https://agrokongo.ao/verificar/{venda.fatura_ref or venda.id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img_buffer = io.BytesIO()
    img = qr.make_image(fill_color="#1B4332", back_color="white")
    img.save(img_buffer, format="PNG")
    qr_base64 = base64.b64encode(img_buffer.getvalue()).decode()

    # 5. Renderizar o HTML
    html = render_template(
        'documentos/fatura_padrao.html',
        venda=venda,
        qr_base64=qr_base64,
        verificacao_hash=verificacao_hash
    )

    # 6. CONFIGURAÇÃO CRÍTICA: Caminho do wkhtmltopdf no Windows
    # O 'r' antes das aspas é obrigatório para caminhos do Windows
    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

    # 7. Opções do PDF
    options = {
        'page-size': 'A4',
        'margin-top': '0mm',
        'margin-right': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm',
        'encoding': "UTF-8",
        'no-outline': None,
        'enable-local-file-access': None,
        'quiet': ''  # Evita logs desnecessários
    }

    # 8. Gerar o binário do PDF com a configuração explícita
    try:
        pdf = pdfkit.from_string(html, False, configuration=config, options=options)
    except Exception as e:
        # Se falhar aqui, verifique se o caminho em path_wkhtmltopdf está correto
        return f"Erro técnico ao gerar PDF: {str(e)}", 500

    # 9. Criar a resposta e forçar o download
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    nome_arquivo = f"Fatura_AgroKongo_{venda.fatura_ref or venda.id}.pdf"
    response.headers['Content-Disposition'] = f'attachment; filename={nome_arquivo}'

    return response

@main_bp.route('/termos-e-condicoes')
def termos():
    return render_template('main/termos.html')