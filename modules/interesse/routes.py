from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from core.models import Usuario, Produto, Interesse, Provincia
from datetime import datetime

# Usamos o blueprint de perfil para manter a organização
from modules.perfil.routes import perfil_bp


@perfil_bp.route('/novo-interesse', methods=['GET', 'POST'])
@login_required
def novo_interesse():
    """Formulário para o comprador registar o que deseja comprar."""

    # 1. Bloqueio de segurança
    if current_user.tipo != 'comprador':
        flash("Apenas compradores podem publicar intenções de compra.", "warning")
        return redirect(url_for('perfil.dashboard'))

    # 2. Dados para os selects do formulário
    produtos = Produto.query.order_by(Produto.nome).all()
    provincias = Provincia.query.order_by(Provincia.nome).all()

    if request.method == 'POST':
        try:
            # Captura de dados do formulário
            produto_id = request.form.get('produto_id')
            quantidade_raw = request.form.get('quantidade_kg')
            # No seu models.py o campo é 'quantidade_pretendida'

            # Validação simples
            if not produto_id or not quantidade_raw:
                flash("Produto e quantidade são obrigatórios.", "danger")
                return render_template('perfil/novo_interesse.html', produtos=produtos, provincias=provincias)

            # Criar o registo (Alinhado com o seu models.py)
            # Nota: O seu model 'Interesse' usa 'safra_id'.
            # Se for uma intenção de compra genérica (sem safra fixa),
            # certifique-se que o seu model suporta safra_id=None ou produto_id.

            novo = Interesse(
                comprador_id=current_user.id,
                safra_id=request.form.get('safra_id'),  # Se vier de um produto específico
                quantidade_pretendida=float(quantidade_raw),
                status='pendente',
                data_criacao=datetime.utcnow()
            )

            db.session.add(novo)
            db.session.commit()

            flash("A sua intenção de compra foi registada com sucesso! 🌱", "success")
            return redirect(url_for('perfil.meu_perfil_comprador'))

        except Exception as e:
            db.session.rollback()
            flash("Ocorreu um erro ao registar o interesse. Verifique os dados.", "danger")
            print(f"DEBUG: {e}")

    return render_template('perfil/novo_interesse.html',
                           produtos=produtos,
                           provincias=provincias)