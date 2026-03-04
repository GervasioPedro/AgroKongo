from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app, abort, send_from_directory, make_response
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf
from wtforms import ValidationError
from sqlalchemy import func
from app.extensions import db
from app.models import (
    Safra, Produto, Notificacao, Provincia,
    Municipio, Usuario, Transacao, TransactionStatus, MovimentacaoFinanceira, aware_utcnow
)
from app.utils.helpers import salvar_ficheiro
from datetime import datetime, timezone
from markupsafe import escape
from urllib.parse import urlparse
import pdfkit
import os
import hashlib
import qrcode
import io
import base64
from decimal import Decimal

main_bp = Blueprint('main', __name__)


@main_bp.route('/health')
@login_required
def health_check():
    if not current_user.is_authenticated or current_user.tipo != 'admin':
        abort(403)
    
    try:
        db.session.execute(db.text('SELECT 1'))
        db_status = 'healthy'
    except Exception:
        db_status = 'unhealthy'
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'database': db_status,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200 if db_status == 'healthy' else 503


@main_bp.route('/')
def index():
    safras_recentes = Safra.query.join(Usuario, Safra.produtor_id == Usuario.id) \
        .filter(Safra.status == 'disponivel', Usuario.conta_validada == True) \
        .order_by(Safra.id.desc()).limit(4).all()
    return render_template('index.html', safras=safras_recentes)


def _get_dashboard_endpoint(tipo):
    endpoints = {
        'admin': 'admin.dashboard',
        'produtor': 'produtor.dashboard',
        'comprador': 'comprador.dashboard'
    }
    return endpoints.get(tipo, 'main.index')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.perfil_completo:
        flash("ℹ️ Quase lá! Complete o seu perfil para começar a negociar.", "info")
        return redirect(url_for('main.completar_perfil'))
    
    if current_user.tipo != 'admin' and not current_user.conta_validada:
        flash("⚠️ Sua conta está pendente de validação pela administração.", "warning")
        return redirect(url_for('main.index'))

    endpoint = _get_dashboard_endpoint(current_user.tipo)
    return redirect(url_for(endpoint))


@main_bp.route('/completar-perfil', methods=['GET', 'POST'])
@login_required
def completar_perfil():
    if current_user.perfil_completo and not request.args.get('editar'):
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        try:
            current_user.provincia_id = request.form.get('provincia_id')
            current_user.municipio_id = request.form.get('municipio_id')
            current_user.nif = escape(request.form.get('nif', '').strip().upper())

            if current_user.tipo == 'produtor':
                current_user.iban = escape(request.form.get('iban', '').replace(" ", "").upper())

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
    notif = Notificacao.query.get_or_404(id)

    if notif.usuario_id != current_user.id:
        abort(403)

    notif.lida = True
    db.session.commit()

    destino = url_for('main.dashboard')
    if notif.link:
        parsed = urlparse(notif.link)
        if not parsed.scheme and not parsed.netloc:
            destino = notif.link
        elif parsed.scheme in ['http', 'https'] and parsed.netloc == request.host:
            destino = notif.link
    
    return redirect(destino)


@main_bp.route('/api/municipios/<int:provincia_id>')
def get_municipios(provincia_id):
    municipios = Municipio.query.filter_by(provincia_id=provincia_id).order_by(Municipio.nome).all()
    return jsonify([{'id': m.id, 'nome': escape(str(m.nome))} for m in municipios])


@main_bp.route('/api/wallet')
@login_required
def api_wallet():
    carteira = current_user.obter_carteira()

    movimentos = MovimentacaoFinanceira.query.filter_by(usuario_id=current_user.id) \
        .order_by(MovimentacaoFinanceira.data_movimentacao.desc()).limit(20).all()

    movimentos_json = []
    for m in movimentos:
        movimentos_json.append({
            'id': str(m.id),
            'tipo': escape(m.tipo) if m.tipo in ['credito', 'debito', 'escrow'] else 'outro',
            'valorKz': float(m.valor),
            'descricao': escape(m.descricao or ''),
            'createdAtISO': m.data_movimentacao.isoformat() if m.data_movimentacao else None
        })

    return jsonify({
        'resumo': {
            'saldoDisponivelKz': float(carteira.saldo_disponivel),
            'saldoEscrowKz': float(getattr(carteira, 'saldo_bloqueado', 0) or 0),
            'pendentes': Transacao.query.filter_by(comprador_id=current_user.id, status=TransactionStatus.PENDENTE).count()
        },
        'movimentos': movimentos_json
    })


@main_bp.route('/perfil')
@login_required
def perfil():
    usuario = current_user
    estatisticas = {}

    if usuario.tipo == 'admin':
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
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
    Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).update({Notificacao.lida: True})
    db.session.commit()
    
    destino = url_for('main.index')
    if request.referrer:
        parsed = urlparse(request.referrer)
        if parsed.netloc == request.host or not parsed.netloc:
            destino = request.referrer
    
    return redirect(destino)


@main_bp.route('/marcar-lidas', methods=['POST'])
@login_required
def marcar_notificacoes_lidas():
    try:
        token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        validate_csrf(token)
    except ValidationError:
        return jsonify({'error': 'CSRF token inválido'}), 403
    
    Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).update({'lida': True})
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Notificações marcadas como lidas'})


@main_bp.route('/produtor/<int:id>')
def perfil_produtor(id):
    produtor = Usuario.query.get_or_404(id)
    
    if produtor.tipo != 'produtor':
        abort(404)
    
    if not produtor.conta_validada:
        abort(404)
    
    avaliacoes = []
    media = 0

    return render_template('main/perfil_produtor.html',
                           produtor=produtor,
                           avaliacoes=avaliacoes,
                           media=media)


@main_bp.route('/media/privado/<subpasta>/<filename>')
@login_required
def servir_privado(subpasta, filename):
    safe_subpasta = os.path.basename(subpasta)
    safe_filename = os.path.basename(filename)
    
    base_dir = os.path.abspath(current_app.config['UPLOAD_FOLDER_PRIVATE'])
    diretorio = os.path.abspath(os.path.join(base_dir, safe_subpasta))
    filepath = os.path.abspath(os.path.join(diretorio, safe_filename))
    
    if not filepath.startswith(base_dir + os.sep):
        abort(403)
    if not os.path.exists(filepath):
        abort(404)
    
    if current_user.tipo == 'admin':
        return send_from_directory(diretorio, safe_filename, as_attachment=False)
    
    if safe_subpasta == 'comprovativos':
        transacao = Transacao.query.filter_by(comprovativo_path=safe_filename).first()
        if not transacao or current_user.id not in [transacao.comprador_id, transacao.vendedor_id]:
            abort(403)
    elif safe_subpasta in ['documentos', 'identidade']:
        if safe_filename != current_user.documento_pdf:
            abort(403)
    else:
        abort(403)

    return send_from_directory(diretorio, safe_filename, as_attachment=False)


@main_bp.route('/media/publico/<subpasta>/<filename>')
def servir_publico(subpasta, filename):
    safe_subpasta = os.path.basename(subpasta)
    safe_filename = os.path.basename(filename)
    
    base_dir = os.path.abspath(current_app.config['UPLOAD_FOLDER_PUBLIC'])
    diretorio = os.path.abspath(os.path.join(base_dir, safe_subpasta))
    filepath = os.path.abspath(os.path.join(diretorio, safe_filename))
    
    if not filepath.startswith(base_dir + os.sep):
        abort(403)
    if not os.path.exists(filepath):
        abort(404)

    return send_from_directory(diretorio, safe_filename)


@main_bp.route('/uploads/perfil/<filename>')
def serve_perfil(filename):
    safe_filename = os.path.basename(filename)
    folder = os.path.abspath(os.path.join(current_app.config['UPLOAD_FOLDER_PUBLIC'], 'perfil'))
    filepath = os.path.abspath(os.path.join(folder, safe_filename))
    
    if not filepath.startswith(folder + os.sep):
        abort(403)
    if not os.path.exists(filepath):
        abort(404)
    
    return send_from_directory(folder, safe_filename)


@main_bp.route('/servir-documento/<filename>')
@login_required
def servir_documento(filename):
    safe_filename = os.path.basename(filename)
    directory = os.path.abspath(os.path.join(current_app.config['UPLOAD_FOLDER_PRIVATE'], 'documentos'))
    filepath = os.path.abspath(os.path.join(directory, safe_filename))
    
    if not filepath.startswith(directory + os.sep):
        abort(403)
    if not os.path.exists(filepath):
        abort(404)
    
    if current_user.tipo != 'admin' and safe_filename != current_user.documento_pdf:
        abort(403)
    
    return send_from_directory(directory, safe_filename)


@main_bp.route('/fatura/visualizar/<int:trans_id>')
@login_required
def visualizar_fatura(trans_id):
    venda = Transacao.query.get_or_404(trans_id)
    
    if current_user.tipo != 'admin' and current_user.id not in [venda.comprador_id, venda.vendedor_id]:
        abort(403)
    
    return render_template('documentos/fatura_geral.html', venda=venda)


@main_bp.route('/gerar_fatura/<int:trans_id>')
@login_required
def baixar_fatura(trans_id):
    venda = Transacao.query.get_or_404(trans_id)

    if current_user.tipo != 'admin' and current_user.id not in [venda.vendedor_id, venda.comprador_id]:
        abort(403)

    hash_seed = f"{venda.id}-{venda.data_criacao}-{venda.valor_total_pago}"
    verificacao_hash = hashlib.sha256(hash_seed.encode()).hexdigest()[:16].upper()

    qr_data = f"https://agrokongo.ao/verificar/{venda.fatura_ref or venda.id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img_buffer = io.BytesIO()
    img = qr.make_image(fill_color="#1B4332", back_color="white")
    img.save(img_buffer, format="PNG")
    qr_base64 = base64.b64encode(img_buffer.getvalue()).decode()

    html = render_template(
        'documentos/fatura_padrao.html',
        venda=venda,
        qr_base64=qr_base64,
        verificacao_hash=verificacao_hash
    )

    path_wkhtmltopdf = current_app.config.get('WKHTMLTOPDF_PATH')
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf) if path_wkhtmltopdf else None

    options = {
        'page-size': 'A4',
        'margin-top': '0mm',
        'margin-right': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm',
        'encoding': "UTF-8",
        'no-outline': None,
        'enable-local-file-access': None,
        'quiet': ''
    }

    try:
        pdf = pdfkit.from_string(html, False, configuration=config, options=options)
    except Exception as e:
        return f"Erro técnico ao gerar PDF: {str(e)}", 500

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    nome_arquivo = f"Fatura_AgroKongo_{venda.fatura_ref or venda.id}.pdf"
    response.headers['Content-Disposition'] = f'attachment; filename={nome_arquivo}'

    return response


@main_bp.route('/termos-e-condicoes')
def termos():
    return render_template('main/termos.html')
