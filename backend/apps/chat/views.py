from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.chat.models import Mensagem


class MensagemSerializer(serializers.ModelSerializer):
    remetente_nome = serializers.CharField(source="remetente.nome", read_only=True)

    class Meta:
        model = Mensagem
        fields = [
            "id", "transacao", "remetente", "remetente_nome", "destinatario",
            "conteudo", "data_envio", "lida",
        ]
        read_only_fields = ["id", "remetente", "data_envio", "lida"]


class MensagemViewSet(viewsets.ModelViewSet):
    serializer_class = MensagemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        from django.db.models import Q

        qs = Mensagem.objects.select_related("remetente")
        if user.eh_admin:
            return qs
        return qs.filter(Q(remetente=user) | Q(destinatario=user))

    def perform_create(self, serializer):
        msg = serializer.save(remetente=self.request.user)
        from apps.notifications.services import notificar

        notificar(msg.destinatario, f"Noova mensagem de {msg.remetente.nome}.",
                  link=f"/dashboard/chat/{msg.transacao_id}")

    @action(detail=True, methods=["post"], url_path="marcar-lida")
    def marcar_lida(self, request, pk=None):
        msg = self.get_object()
        msg.lida = True
        msg.save(update_fields=["lida"])
        return Response(MensagemSerializer(msg).data)
