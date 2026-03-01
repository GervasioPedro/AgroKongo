# app/forms.py - Forms leves, seguros, HTMX-ready e super aconchegantes
# Versão Corrigida - 22/02/2026
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField, DecimalField, DateField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp, NumberRange, Optional
import re


# ====================== AUTH ======================
class LoginForm(FlaskForm):
    """Formulário de login seguro com validação de telemóvel Angola."""
    telemovel = StringField('Telemóvel', validators=[
        DataRequired(message="O telemóvel é obrigatório."),
        Length(min=9, max=9, message="Deve ter exatamente 9 dígitos."),
        Regexp(r'^9[1-9]\d{7}$', message="Telemóvel inválido para Angola.")
    ])
    senha = PasswordField('Senha', validators=[
        DataRequired(message="A senha é obrigatória.")
    ])
    submit = SubmitField('Entrar')


class RegistoForm(FlaskForm):
    """Formulário de registro com validação forte de senha."""
    nome = StringField('Nome completo', validators=[
        DataRequired(message="O nome é obrigatório."),
        Length(min=3, max=100, message="Nome deve ter entre 3 e 100 caracteres.")
    ])
    telemovel = StringField('Telemóvel', validators=[
        DataRequired(message="O telemóvel é obrigatório."),
        Length(min=9, max=9, message="Deve ter exatamente 9 dígitos."),
        Regexp(r'^9[1-9]\d{7}$', message="Telemóvel inválido para Angola.")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="O email é obrigatório."),
        Email(message="Email inválido.")
    ])
    senha = PasswordField('Senha', validators=[
        DataRequired(message="A senha é obrigatória."),
        Length(min=12, message="Mínimo 12 caracteres."),
        Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,}$',
            message="Deve ter maiúscula, minúscula, número e símbolo."
        )
    ])
    confirmar_senha = PasswordField('Confirmar senha', validators=[
        DataRequired(message="Confirme a senha."),
        EqualTo('senha', message="As senhas não coincidem.")
    ])
    tipo = SelectField('Tipo de conta', choices=[
        ('produtor', 'Produtor'),
        ('comprador', 'Comprador')
    ], validators=[DataRequired(message="Selecione o tipo de conta.")])
    termos = BooleanField('Li e aceito os Termos e a Política de Privacidade', validators=[
        DataRequired(message="Deve aceitar os termos.")
    ])
    submit = SubmitField('Registar')

    def validate_telemovel(self, field):
        """Valida se telemóvel já existe no banco."""
        from app.models import Usuario
        if Usuario.query.filter_by(telemovel=field.data).first():
            raise ValidationError('Este telemóvel já está registado.')

    def validate_email(self, field):
        """Valida se email já existe no banco."""
        from app.models import Usuario
        if Usuario.query.filter_by(email=field.data).first():
            raise ValidationError('Este email já está registado.')


class AlterarSenhaForm(FlaskForm):
    """Formulário para alteração de senha."""
    senha_atual = PasswordField('Senha Atual', validators=[
        DataRequired(message="A senha atual é obrigatória.")
    ])
    nova_senha = PasswordField('Nova Senha', validators=[
        DataRequired(message="A nova senha é obrigatória."),
        Length(min=12, message="Mínimo 12 caracteres."),
        Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,}$',
            message="Deve ter maiúscula, minúscula, número e símbolo."
        )
    ])
    confirmar_senha = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(message="Confirme a nova senha."),
        EqualTo('nova_senha', message="As senhas não coincidem.")
    ])
    submit = SubmitField('Alterar Senha')


class OTPForm(FlaskForm):
    """Formulário de verificação OTP (6 dígitos)."""
    otp = StringField('Código OTP', validators=[
        DataRequired(message="O código OTP é obrigatório."),
        Length(min=6, max=6, message="O código deve ter 6 dígitos."),
        Regexp(r'^\d{6}$', message="O código deve conter apenas números.")
    ])
    submit = SubmitField('Verificar OTP')


# ====================== PERFIL ======================
class PerfilForm(FlaskForm):
    """Formulário de completar/editar perfil (KYC)."""
    nif = StringField('NIF (10 dígitos)', validators=[
        DataRequired(message="O NIF é obrigatório."),
        Length(min=10, max=10, message="NIF deve ter exatamente 10 dígitos."),
        Regexp(r'^\d{10}$', message="NIF deve conter apenas números.")
    ])
    iban = StringField('IBAN (Angola)', validators=[
        DataRequired(message="O IBAN é obrigatório."),
        Regexp(r'^AO\d{21}$', message="IBAN inválido para Angola (AO06 + 21 dígitos).")
    ])
    provincia_id = SelectField('Província', coerce=int, validators=[
        DataRequired(message="Selecione a província.")
    ])
    municipio_id = SelectField('Município', coerce=int, validators=[
        DataRequired(message="Selecione o município.")
    ])
    foto_perfil = FileField('Foto de perfil (opcional)', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'webp'], message="Apenas imagens JPG, PNG ou WEBP.")
    ])
    documento_pdf = FileField('Documento PDF', validators=[
        FileAllowed(['pdf'], message="Apenas arquivos PDF.")
    ])
    submit = SubmitField('Salvar Perfil')

    def validate_nif(self, field):
        """Valida checksum do NIF angolano."""
        nif = field.data
        if len(nif) != 10:
            raise ValidationError('NIF deve ter 10 dígitos.')
        soma = sum(int(d) * (10 - i) for i, d in enumerate(nif[:9]))
        check = (11 - (soma % 11)) % 10
        if int(nif[9]) != check:
            raise ValidationError('NIF inválido (checksum falhou).')

    def validate_iban(self, field):
        """Valida checksum do IBAN angolano."""
        iban = field.data.upper().replace(' ', '')
        if not re.match(r'^AO06\d{21}$', iban):
            raise ValidationError('IBAN deve ser AO06 + 21 dígitos.')
        # Checksum ISO 13616
        rearranged = iban[4:] + iban[:4]
        num_str = ''.join(str(10 + ord(c) - ord('A')) if c.isalpha() else c for c in rearranged)
        if int(num_str) % 97 != 1:
            raise ValidationError('IBAN checksum inválido.')


# ====================== MERCADO ======================
class ReservaForm(FlaskForm):
    """Formulário de reserva de safra."""
    quantidade = DecimalField('Quantidade (kg)', validators=[
        DataRequired(message="A quantidade é obrigatória."),
        NumberRange(min=0.01, message="Quantidade deve ser maior que zero.")
    ])
    submit = SubmitField('Reservar')


class ComprovativoForm(FlaskForm):
    """Formulário de submissão de comprovativo de pagamento."""
    comprovativo = FileField('Comprovativo (JPG/PNG/PDF)', validators=[
        FileRequired(message="O comprovativo é obrigatório."),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], message="Apenas JPG, PNG ou PDF.")
    ])
    valor_pago = DecimalField('Valor pago', validators=[
        DataRequired(message="O valor pago é obrigatório."),
        NumberRange(min=0.01, message="Valor deve ser maior que zero.")
    ])
    data_pagamento = DateField('Data do pagamento', validators=[
        DataRequired(message="A data do pagamento é obrigatória.")
    ], format='%Y-%m-%d')
    submit = SubmitField('Submeter Comprovativo')


# ====================== AVALIAÇÃO E DISPUTA ======================
class AvaliacaoForm(FlaskForm):
    """Formulário de avaliação de vendedor."""
    nota = SelectField('Nota', choices=[
        (1, '1 - Muito ruim'),
        (2, '2 - Ruim'),
        (3, '3 - Regular'),
        (4, '4 - Bom'),
        (5, '5 - Excelente')
    ], coerce=int, validators=[
        DataRequired(message="A nota é obrigatória.")
    ])
    comentario = TextAreaField('Comentário (opcional)', validators=[
        Length(max=500, message="Comentário deve ter no máximo 500 caracteres.")
    ])
    submit = SubmitField('Enviar Avaliação')


class DisputaForm(FlaskForm):
    """Formulário de abertura de disputa."""
    motivo = TextAreaField('Motivo da disputa', validators=[
        DataRequired(message="O motivo é obrigatório."),
        Length(min=20, max=1000, message="Motivo deve ter entre 20 e 1000 caracteres.")
    ])
    submit = SubmitField('Abrir Disputa')


# ====================== PRODUTOR ======================
class SafraForm(FlaskForm):
    """Formulário de criação/edição de safra."""
    produto_id = SelectField('Produto', coerce=int, validators=[
        DataRequired(message="Selecione o produto.")
    ])
    quantidade_disponivel = DecimalField('Quantidade Disponível (kg)', validators=[
        DataRequired(message="A quantidade é obrigatória."),
        NumberRange(min=0.01, message="Quantidade deve ser maior que zero.")
    ])
    preco_por_unidade = DecimalField('Preço por Unidade (Kz)', validators=[
        DataRequired(message="O preço é obrigatório."),
        NumberRange(min=0.01, message="Preço deve ser maior que zero.")
    ])
    descricao = TextAreaField('Descrição', validators=[
        Length(max=1000, message="Descrição deve ter no máximo 1000 caracteres.")
    ])
    imagem = FileField('Imagem da Safra', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], message="Apenas imagens JPG, PNG ou WEBP.")
    ])
    submit = SubmitField('Publicar Safra')


class GuiaRemessaForm(FlaskForm):
    """Formulário de geração de guia de remessa."""
    transportadora = StringField('Transportadora', validators=[
        Optional()
    ])
    matricula_veiculo = StringField('Matrícula do Veículo', validators=[
        Optional(),
        Length(max=20, message="Matrícula deve ter no máximo 20 caracteres.")
    ])
    submit = SubmitField('Gerar Guia')


# ====================== ADMIN ======================
class AdminKYCForm(FlaskForm):
    """Formulário de validação KYC para admin."""
    kyc_status = SelectField('Status KYC', choices=[
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado')
    ], validators=[
        DataRequired(message="Selecione o status.")
    ])
    observacao = TextAreaField('Observação', validators=[
        Length(max=500, message="Observação deve ter no máximo 500 caracteres.")
    ])
    submit = SubmitField('Atualizar KYC')


class AdminDisputaForm(FlaskForm):
    """Formulário de resolução de disputa para admin."""
    decisao = SelectField('Decisão', choices=[
        ('comprador', 'A favor do Comprador'),
        ('vendedor', 'A favor do Vendedor')
    ], validators=[
        DataRequired(message="Selecione a decisão.")
    ])
    motivo = TextAreaField('Motivo da Decisão', validators=[
        DataRequired(message="O motivo é obrigatório."),
        Length(min=20, max=1000, message="Motivo deve ter entre 20 e 1000 caracteres.")
    ])
    submit = SubmitField('Resolver Disputa')


class ContatoForm(FlaskForm):
    """Formulário de contato para página pública."""
    nome = StringField('Nome', validators=[
        DataRequired(message="O nome é obrigatório."),
        Length(min=3, max=100, message="Nome deve ter entre 3 e 100 caracteres.")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="O email é obrigatório."),
        Email(message="Email inválido.")
    ])
    assunto = SelectField('Assunto', choices=[
        ('suporte', 'Suporte Técnico'),
        ('parceria', 'Parceria Comercial'),
        ('denuncia', 'Denúncia'),
        ('outro', 'Outro')
    ], validators=[
        DataRequired(message="Selecione o assunto.")
    ])
    mensagem = TextAreaField('Mensagem', validators=[
        DataRequired(message="A mensagem é obrigatória."),
        Length(min=10, max=2000, message="Mensagem deve ter entre 10 e 2000 caracteres.")
    ])
    submit = SubmitField('Enviar Mensagem')