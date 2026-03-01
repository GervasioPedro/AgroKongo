# app/routes/cadastro_produtor.py - Fluxo completo de cadastro de produtor
# Implementação exata conforme caso de uso especificado

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Usuario, Provincia, Municipio, LogAuditoria
from app.models import Carteira, StatusConta
from app.services.otp_service import gerar_e_enviar_otp, reenviar_otp, OTPService
from app.forms import OTPForm
from app.utils.helpers import salvar_ficheiro
from decimal import Decimal

cadastro_bp = Blueprint('cadastro', __name__)


@cadastro_bp.route('/criar-conta-produtor', methods=['GET', 'POST'])
def criar_conta_produtor():
    """
    Passo 1: Criar Conta como Produtor
    Validação de contato via OTP
    """
    if request.method == 'POST':
        from flask_wtf.csrf import validate_csrf
        from wtforms import ValidationError
        
        # Proteção CSRF - validar ANTES de qualquer processamento
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            abort(403)
        
        telemovel = request.form.get('telemovel', '').strip()
        
        # RN01: Formato do número (9 dígitos, começa com 9)
        if not telemovel.startswith('9') or len(telemovel) != 9:
            flash('Insira um número de telemóvel válido (9 dígitos, começa com 9).', 'warning')
            return render_template('cadastro/passo_1_contato.html')
        
        # Verificar duplicidade (Exceção 5B)
        if Usuario.query.filter_by(telemovel=telemovel).first():
            flash('Este número de telemóvel ou BI já possui uma conta na AgroKongo.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Gerar e enviar OTP
        resultado = gerar_e_enviar_otp(
            telemovel=telemovel,
            canal='whatsapp',  # Pode ser 'sms' também
            ip_address=request.remote_addr
        )
        
        if resultado['sucesso']:
            # Armazenar telemovel na sessão para próximos passos APENAS após sucesso
            from flask import session
            session['cadastro_telemovel'] = telemovel
            session['cadastro_canal'] = 'whatsapp'
            
            flash(f'Código enviado via WhatsApp! Verifique seu celular.', 'success')
            return redirect(url_for('cadastro.validar_otp'))
        else:
            flash(resultado['mensagem'], 'danger')
            return render_template('cadastro/passo_1_contato.html')
    
    return render_template('cadastro/passo_1_contato.html')


@cadastro_bp.route('/validar-otp', methods=['GET', 'POST'])
def validar_otp():
    """
    Passo 2: Validação de contato via OTP
    Exceção 2A: OTP inválido ou expirado
    """
    from flask import session
    
    telemovel = session.get('cadastro_telemovel')
    
    if not telemovel:
        flash('Sessão expirada. Comece novamente.', 'warning')
        return redirect(url_for('cadastro.criar_conta_produtor'))
    
    otp_form = OTPForm()
    
    if request.method == 'POST':
        # Proteção CSRF explícita
        if not otp_form.validate_on_submit():
            flash('Requisição inválida. Tente novamente.', 'danger')
            return render_template('cadastro/passo_2_otp.html', otp_form=otp_form)
        
        codigo = otp_form.otp.data
        
        # Validar OTP
        resultado = OTPService.validar_otp(
            telemovel=telemovel,
            codigo_informado=codigo,
            ip_address=request.remote_addr
        )
        
        if resultado['valido']:
            # OTP válido, continuar para dados básicos
            flash('Telefone validado! Preencha seus dados básicos.', 'success')
            return redirect(url_for('cadastro.dados_basicos'))
        else:
            flash(resultado['mensagem'], 'danger')
            
            # Se esgotou tentativas, limpar e recomeçar
            if resultado['tentativas_restantes'] == 0:
                flash('Número máximo de tentativas. Solicite um novo código.', 'warning')
                return redirect(url_for('cadastro.criar_conta_produtor'))
    
    return render_template('cadastro/passo_2_otp.html', otp_form=otp_form)


@cadastro_bp.route('/reenviar-otp', methods=['POST'])
def reenviar_codigo():
    """
    Reenvia código OTP (Exceção 2A)
    Limite de 3 tentativas para evitar custos de SMS
    """
    from flask import session
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    # Proteção CSRF - validar ANTES de qualquer processamento
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
    telemovel = session.get('cadastro_telemovel')
    canal = session.get('cadastro_canal', 'whatsapp')
    
    if not telemovel:
        flash('Sessão inválida', 'danger')
        return redirect(url_for('cadastro.criar_conta_produtor'))
    
    resultado = reenviar_otp(telemovel, canal, request.remote_addr)
    
    if resultado['sucesso']:
        flash('Novo código enviado!', 'success')
    else:
        flash(resultado['mensagem'], 'danger')
    
    return redirect(url_for('cadastro.validar_otp'))


@cadastro_bp.route('/dados-basicos', methods=['GET', 'POST'])
def dados_basicos():
    """
    Passo 3: Dados Básicos
    Nome Completo, Província, Município, Principal Cultura
    """
    from flask import session
    
    telemovel = session.get('cadastro_telemovel')
    
    if not telemovel:
        flash('Sessão expirada. Comece novamente.', 'warning')
        return redirect(url_for('cadastro.criar_conta_produtor'))
    
    # Obter províncias e municípios
    provincias = Provincia.query.order_by(Provincia.nome).all()
    
    if request.method == 'POST':
        from flask_wtf.csrf import validate_csrf
        from wtforms import ValidationError
        
        # Proteção CSRF
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            abort(403)
        
        nome = request.form.get('nome', '').strip()
        provincia_id = request.form.get('provincia_id')
        municipio_id = request.form.get('municipio_id')
        principal_cultura = request.form.get('principal_cultura', '').strip()
        
        # Validações básicas
        if not nome or len(nome) < 3:
            flash('Nome completo é obrigatório (mínimo 3 caracteres).', 'warning')
            return render_template('cadastro/passo_3_dados_basicos.html', provincias=provincias)
        
        if not provincia_id or not municipio_id:
            flash('Selecione província e município.', 'warning')
            return render_template('cadastro/passo_3_dados_basicos.html', provincias=provincias)
        
        if not principal_cultura:
            flash('Informe sua principal cultura.', 'warning')
            return render_template('cadastro/passo_3_dados_basicos.html', provincias=provincias)
        
        # Armazenar dados na sessão
        session['cadastro_dados'] = {
            'nome': nome,
            'provincia_id': int(provincia_id),
            'municipio_id': int(municipio_id),
            'principal_cultura': principal_cultura
        }
        
        flash('Dados básicos salvos! Defina sua senha.', 'success')
        return redirect(url_for('cadastro.definir_senha'))
    
    return render_template('cadastro/passo_3_dados_basicos.html', provincias=provincias)


@cadastro_bp.route('/definir-senha', methods=['GET', 'POST'])
def definir_senha():
    """
    Passo 4: Segurança (Password)
    PIN de 4 a 6 dígitos (mais fácil de memorizar)
    """
    from flask import session
    
    dados = session.get('cadastro_dados')
    
    if not dados:
        flash('Dados básicos não preenchidos. Comece novamente.', 'warning')
        return redirect(url_for('cadastro.criar_conta_produtor'))
    
    if request.method == 'POST':
        from flask_wtf.csrf import validate_csrf
        from wtforms import ValidationError
        
        # Proteção CSRF
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            abort(403)
        
        senha = request.form.get('senha', '').strip()
        confirmar_senha = request.form.get('confirmar_senha', '').strip()
        
        # Validação de senha (PIN 4-6 dígitos)
        if not senha or not senha.isdigit() or len(senha) < 4 or len(senha) > 6:
            flash('Use um PIN de 4 a 6 dígitos numéricos.', 'warning')
            return render_template('cadastro/passo_4_senha.html')
        
        if senha != confirmar_senha:
            flash('Senhas não conferem.', 'warning')
            return render_template('cadastro/passo_4_senha.html')
        
        # Armazenar senha na sessão
        session['cadastro_senha'] = senha
        
        flash('Senha definida! Agora preencha os dados financeiros.', 'success')
        return redirect(url_for('cadastro.dados_financeiros'))
    
    return render_template('cadastro/passo_4_senha.html')


@cadastro_bp.route('/dados-financeiros', methods=['GET', 'POST'])
def dados_financeiros():
    """
    Passo 5: Dados Financeiros (KYC)
    IBAN e upload do Bilhete de Identidade
    """
    from flask import session
    
    if not _validar_sessao_cadastro(session):
        flash('Dados incompletos. Comece novamente.', 'warning')
        return redirect(url_for('cadastro.criar_conta_produtor'))
    
    if request.method == 'POST':
        return _processar_dados_financeiros(session)
    
    return render_template('cadastro/passo_5_kyc.html')


def _validar_sessao_cadastro(session):
    """Valida se sessão tem todos os dados necessários."""
    return all([
        session.get('cadastro_dados'),
        session.get('cadastro_senha'),
        session.get('cadastro_telemovel')
    ])


def _processar_dados_financeiros(session):
    """Processa formulário de dados financeiros."""
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    # Proteção CSRF - validar ANTES de qualquer processamento
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
    iban = request.form.get('iban', '').strip().upper()
    bi_file = request.files.get('bi_file')
    
    # Validar IBAN
    erro_iban = _validar_iban_angolano(iban)
    if erro_iban:
        flash(erro_iban, 'error')
        return render_template('cadastro/passo_5_kyc.html')
    
    # Validar e salvar BI
    bi_path = _processar_arquivo_bi(bi_file)
    if not bi_path:
        return render_template('cadastro/passo_5_kyc.html')
    
    # Armazenar dados financeiros
    session['cadastro_financeiros'] = {'iban': iban, 'bi_path': bi_path}
    
    # Criar usuário
    return _finalizar_cadastro(session)


def _validar_iban_angolano(iban):
    """Valida formato do IBAN angolano. Retorna mensagem de erro ou None."""
    if not iban:
        return 'IBAN é obrigatório.'
    
    if not iban.startswith('AO06') or len(iban) != 27:
        return 'IBAN inválido. Use formato AO06 + 21 dígitos.'
    
    if not iban[6:].isdigit():
        return 'IBAN inválido. Verifique os dígitos.'
    
    return None


def _processar_arquivo_bi(bi_file):
    """Valida e salva arquivo do BI. Retorna path ou None."""
    if not bi_file:
        flash('Upload do Bilhete de Identidade é obrigatório.', 'warning')
        return None
    
    if not _validar_arquivo_bi(bi_file):
        flash('Arquivo inválido. Envie PDF ou imagem (JPG/PNG).', 'error')
        return None
    
    try:
        return salvar_ficheiro(bi_file, subpasta='documentos_bi', privado=True)
    except Exception as e:
        current_app.logger.error(f"Erro ao salvar BI: {e}")
        flash('Erro ao fazer upload do documento. Tente novamente.', 'error')
        return None


def _finalizar_cadastro(session):
    """Cria usuário, limpa sessão e faz login."""
    try:
        usuario = _criar_usuario_produtor(
            telemovel=session['cadastro_telemovel'],
            dados=session['cadastro_dados'],
            senha=session['cadastro_senha'],
            financeiros=session['cadastro_financeiros']
        )
        
        # Limpar sessão
        for key in ['cadastro_telemovel', 'cadastro_dados', 'cadastro_senha', 'cadastro_financeiros', 'cadastro_canal']:
            session.pop(key, None)
        
        login_user(usuario)
        
        flash('Conta criada! A nossa equipa vai rever o seu BI. Já pode ver os preços, mas só poderá publicar produtos após a nossa validação.', 'success')
        return redirect(url_for('produtor.dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Erro ao criar usuário: {e}")
        flash('Erro ao criar conta. Tente novamente.', 'error')
        return render_template('cadastro/passo_5_kyc.html')


def _validar_arquivo_bi(file) -> bool:
    """
    Valida arquivo do Bilhete de Identidade
    Aceita: PDF, JPG, PNG (máximo 5MB)
    """
    if not file or not file.filename:
        return False
    
    # Verificar extensão
    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png'}
    if file.filename.split('.')[-1].lower() not in allowed_extensions:
        return False
    
    # Verificar tamanho (5MB)
    file.seek(0, 2)  # Reset file pointer
    file_size = len(file.read())
    file.seek(0)  # Reset again
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        return False
    
    return True


def _criar_usuario_produtor(telemovel: str, dados: dict, senha: str, financeiros: dict) -> Usuario:
    """
    RN02: Criação do usuário e carteira de forma atômica
    Se um falhar, falha o outro
    """
    try:
        # Iniciar transação atômica
        db.session.begin_nested()
        
        # Criar usuário
        usuario = Usuario(
            nome=dados['nome'],
            telemovel=telemovel,
            tipo='produtor',
            provincia_id=dados['provincia_id'],
            municipio_id=dados['municipio_id'],
            iban=financeiros['iban'],
            documento_pdf=financeiros['bi_path'],
            status_conta=StatusConta.PENDENTE_VERIFICACAO,  # Status inicial
            perfil_completo=True,  # Dados completos
            conta_validada=False  # Aguardando validação admin
        )
        usuario.senha = senha  # Hash automático
        
        db.session.add(usuario)
        db.session.flush()  # Obter ID sem commit
        
        # RN02: Criar carteira na mesma transação
        carteira = Carteira(
            usuario_id=usuario.id,
            saldo_disponivel=Decimal('0.00'),  # Carteira com saldo 0.00
            saldo_bloqueado=Decimal('0.00')
        )
        
        db.session.add(carteira)
        
        # Log de auditoria
        db.session.add(LogAuditoria(
            usuario_id=usuario.id,
            acao="CADASTRO_PRODUTOR",
            detalhes=f"Produtor cadastrado: {dados['nome']} | Status: {StatusConta.PENDENTE_VERIFICACAO}"
        ))
        
        # Commit final (ambos ou nenhum)
        db.session.commit()
        
        current_app.logger.info(f"Produtor criado com sucesso: {usuario.nome} (ID: {usuario.id})")
        return usuario
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro na criação do produtor: {e}")
        raise e


@cadastro_bp.route('/verificar-iban', methods=['GET'])
def verificar_iban():
    """
    API endpoint para validação de IBAN (Exceção 5A)
    Validação em tempo real via AJAX
    """
    from flask import jsonify
    
    iban = request.args.get('iban', '').strip().upper()
    
    if not iban:
        return jsonify({'valido': False, 'mensagem': 'IBAN é obrigatório'})
    
    # RN02: Validação IBAN angolano
    if not iban.startswith('AO06') or len(iban) != 27:
        return jsonify({'valido': False, 'mensagem': 'IBAN inválido. Use formato AO06 + 21 dígitos'})
    
    if not iban[6:].isdigit():
        return jsonify({'valido': False, 'mensagem': 'IBAN inválido. Verifique os dígitos'})
    
    return jsonify({'valido': True, 'mensagem': 'IBAN válido'})
