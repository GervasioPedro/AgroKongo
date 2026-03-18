"""
Serviço de Gestão de Usuários
Responsável por validação, criação e gestão de perfis.
"""
from typing import Tuple, Optional, List
from flask import current_app
import os

from app.extensions import db
from app.models import Usuario, Notificacao, LogAuditoria


class UsuarioService:
    """Serviço responsável por gerir o ciclo de vida de usuários."""
    
    @staticmethod
    def validar_usuario(user_id: int, admin_id: int) -> Tuple[bool, Optional[str]]:
        """
        Valida a conta de um usuário.
        
        Args:
            user_id: ID do usuário a validar
            admin_id: ID do admin que está validando
            
        Returns:
            Tuple[success, mensagem]
        """
        try:
            user = Usuario.query.get_or_404(user_id)
            user.conta_validada = True
            
            db.session.add(Notificacao(
                usuario_id=user.id,
                mensagem="Sua conta foi validada com sucesso! Já pode operar no mercado."
            ))
            
            db.session.add(LogAuditoria(
                usuario_id=admin_id,
                acao="Validação de Conta",
                detalhes=f"Validou o perfil de {user.nome}",
                ip=None
            ))
            
            db.session.commit()
            
            return True, f"Utilizador {user.nome} validado com sucesso!"
            
        except Exception as e:
            current_app.logger.error(f"Erro validar user: {e}")
            db.session.rollback()
            return False, "Erro ao validar utilizador."
    
    @staticmethod
    def rejeitar_usuario(user_id: int, admin_id: int, motivo: str) -> Tuple[bool, Optional[str]]:
        """
        Rejeita o perfil de um usuário.
        
        Args:
            user_id: ID do usuário
            admin_id: ID do admin
            motivo: Motivo da rejeição
            
        Returns:
            Tuple[success, mensagem]
        """
        try:
            user = Usuario.query.get_or_404(user_id)
            user.perfil_completo = False
            user.conta_validada = False
            
            db.session.add(Notificacao(
                usuario_id=user.id,
                mensagem=f"⚠️ Seu perfil foi rejeitado. Motivo: {motivo}"
            ))
            
            db.session.add(LogAuditoria(
                usuario_id=admin_id,
                acao="Rejeição de Perfil",
                detalhes=f"Rejeitou o perfil de {user.nome}. Motivo: {motivo}",
                ip=None
            ))
            
            db.session.commit()
            
            return True, f"Utilizador {user.nome} notificado da rejeição."
            
        except Exception as e:
            current_app.logger.error(f"Erro rejeitar user: {e}")
            db.session.rollback()
            return False, "Erro ao rejeitar utilizador."
    
    @staticmethod
    def eliminar_usuario(user_id: int, admin_id: int, upload_base_path: str) -> Tuple[bool, Optional[str]]:
        """
        Elimina um usuário e seus ficheiros associados.
        
        Args:
            user_id: ID do usuário
            admin_id: ID do admin
            upload_base_path: Caminho base para uploads
            
        Returns:
            Tuple[success, mensagem]
        """
        try:
            usuario = Usuario.query.get_or_404(user_id)
            
            # Limpeza de Ficheiros Físicos
            if usuario.foto_perfil:
                caminho_foto = os.path.join(upload_base_path, 'public', 'perfil', usuario.foto_perfil)
                if os.path.exists(caminho_foto):
                    try:
                        os.remove(caminho_foto)
                    except Exception as e:
                        current_app.logger.warning(f"Falha ao remover foto: {e}")
            
            if usuario.documento_pdf:
                caminho_pdf = os.path.join(upload_base_path, 'private', 'documentos', usuario.documento_pdf)
                if os.path.exists(caminho_pdf):
                    try:
                        os.remove(caminho_pdf)
                    except Exception as e:
                        current_app.logger.warning(f"Falha ao remover PDF: {e}")
            
            db.session.delete(usuario)
            
            db.session.add(LogAuditoria(
                usuario_id=admin_id,
                acao="DELETE_USER",
                detalhes=f"Eliminou user {usuario.nome} (ID: {user_id})",
                ip=None
            ))
            
            return True, f"Utilizador {usuario.nome} eliminado com sucesso."
            
        except Exception as e:
            current_app.logger.error(f"Erro ao eliminar user: {e}")
            return False, f"Erro ao eliminar utilizador: {str(e)}"
    
    @staticmethod
    def verificar_perfil_completo(usuario: Usuario) -> bool:
        """
        Verifica se o perfil do usuário está completo.
        
        Args:
            usuario: Instância do usuário
            
        Returns:
            bool: True se perfil estiver completo
        """
        return usuario.verificar_e_atualizar_perfil()
