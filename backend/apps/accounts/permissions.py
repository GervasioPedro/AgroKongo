"""Permissões por perfil (RBAC) — substitui `role_required`/`kyc_required` do Flask."""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    message = "Acesso restrito a administradores."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.eh_admin)


class IsProdutor(permissions.BasePermission):
    message = "Apenas produtores podem executar esta ação."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.eh_produtor or user.eh_admin))


class IsComprador(permissions.BasePermission):
    message = "Apenas compradores podem executar esta ação."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.eh_comprador or user.eh_admin))


class KYCAprovado(permissions.BasePermission):
    """Bloqueia ações comerciais sem validação de identidade (substitui kyc_required)."""

    message = "Complete a verificação de identidade (KYC) antes de continuar."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return user.kyc_aprovado or user.eh_admin
