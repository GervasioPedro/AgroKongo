# AgroKongo 🚜🇦🇴

Plataforma de intermediação agrícola com sistema de **Pagamento Seguro (Custódia)**.

## 🚀 Sobre o Projeto
O AgroKongo facilita a ligação entre produtores e compradores em Angola, garantindo que as transações financeiras sejam seguras. O capital do comprador fica retido pelo sistema (Admin) e só é libertado ao produtor após a confirmação da entrega.

## 🛡️ Fluxo de Pagamento Seguro
1. **Interesse**: O comprador manifesta interesse numa safra.
2. **Aprovação**: O produtor aceita a proposta e uma fatura é gerada.
3. **Pagamento**: O comprador faz o pagamento (Express ou Transferência) e anexa o comprovativo.
4. **Custódia**: O Administrador valida o comprovativo. O status muda para `pago_custodia`.
5. **Entrega**: O produtor entrega a mercadoria.
6. **Finalização**: O comprador confirma a receção e o ciclo encerra.

## 🛠️ Tecnologias Utilizadas
- **Python / Flask** (Backend)
- **SQLAlchemy** (ORM / Base de Dados)
- **Flask-Login** (Autenticação)
- **Werkzeug** (Segurança de Passwords)
- **Bootstrap 5** (Interface)

## 📦 Como Instalar
1. Clone o repositório: `git clone https://github.com/teu-usuario/agrokongo.git`
2. Crie um ambiente virtual: `python -m venv .venv`
3. Ative o ambiente e instale as dependências: `pip install -r requirements.txt`
4. Inicie o app: `flask run`