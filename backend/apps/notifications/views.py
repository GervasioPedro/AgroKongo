from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notifications.models import Notificacao


class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = ["id", "mensagem", "link", "lida", "criado_em"]
        read_only_fields = ["id", "mensagem", "link", "criado_em"]


class NotificacaoViewSet(viewsets.ModelViewSet):
    serializer_class = NotificacaoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Notificacao.objects.filter(utilizador=self.request.user)

    @action(detail=False, methods=["post"], url_path="marcar-todas-lidas")
    def marcar_todas_lidas(self, request):
        atualizadas = self.get_queryset().filter(lida=False).update(lida=True)
        return Response({"marcadas": atualizadas})
