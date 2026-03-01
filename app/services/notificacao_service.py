from typing import Optional
from app.extensions import db
from app.models import Notificacao, Usuario

def marcar_notificacao_como_lida(usuario: Usuario, notificacao_id: int) -> Optional[Notificacao]:
    """
    Marca uma notificação específica como lida, garantindo que pertence ao usuário.
    Orquestra a lógica de negócio e a transação com a base de dados.
    
    Args:
        usuario: Instância do usuário atual.
        notificacao_id: ID da notificação a ser lida.
        
    Returns:
        Notificacao atualizada ou None se não encontrada/não autorizada.
    """
    # 1. Busca segura (apenas notificações do próprio usuário)
    notificacao = Notificacao.query.filter_by(
        id=notificacao_id, 
        usuario_id=usuario.id
    ).first()

    if not notificacao:
        return None

    # 2. Lógica de Domínio (Idempotência: se já leu, não faz nada)
    if notificacao.lida:
        return notificacao

    # 3. Aplicação da mudança de estado
    notificacao.marcar_como_lida()

    # 4. Persistência (Commit) controlada pelo Serviço
    db.session.commit()
    
    return notificacao