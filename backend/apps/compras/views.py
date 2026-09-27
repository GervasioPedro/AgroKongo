"""API de transações: compra, confirmação de pagamento/envio/entrega e disputa."""
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import KYCAprovado
from apps.compras.models import Comprovativo, Transacao
from apps.compras.services import CompraService, ErroCompra


class TransacaoSerializer(serializers.ModelSerializer):
    produto = serializers.CharField(source="safra.produto.nome", read_only=True)
    comprador_nome = serializers.CharField(source="comprador.nome", read_only=True)
    vendedor_nome = serializers.CharField(source="vendedor.nome", read_only=True)

    class Meta:
        model = Transacao
        fields = [
            "id", "fatura_ref", "safra", "produto", "quantidade_comprada",
            "valor_total_pago", "comissao_plataforma", "valor_liquido_vendedor",
            "status", "criado_em", "data_pagamento_escrow", "data_envio",
            "data_entrega", "data_liquidacao", "previsao_entrega",
            "comprador", "comprador_nome", "vendedor", "vendedor_nome",
        ]
        read_only_fields = fields


class HistoricoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transacao._meta.get_field("historico").related_model
        fields = ["status_anterior", "status_novo", "data_mudanca", "observacao"]


class TransacaoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transacao.objects.select_related(
        "safra__produto", "comprador", "vendedor"
    ).all()
    serializer_class = TransacaoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status"]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        from django.db.models import Q

        # Filtros por papel (usados pelo frontend React: compras/vendas do utilizador)
        comprador = self.request.query_params.get("comprador")
        vendedor = self.request.query_params.get("vendedor")
        if comprador == "meu":
            comprador = str(user.pk)
        if vendedor == "meu":
            vendedor = str(user.pk)
        if comprador:
            qs = qs.filter(comprador_id=comprador)
        elif vendedor:
            qs = qs.filter(vendedor_id=vendedor)
        elif not user.eh_admin:
            qs = qs.filter(Q(comprador=user) | Q(vendedor=user))
        return qs

    @action(detail=True, methods=["get"], url_path="historico")
    def historico(self, request, pk=None):
        obj = self.get_object()
        return Response(HistoricoSerializer(obj.historico, many=True).data)

    @action(detail=False, methods=["post"], url_path="reservar",
            permission_classes=[IsAuthenticated, KYCAprovado])
    def reservar(self, request):
        safra_id = request.data.get("safra_id") or request.data.get("safra")
        quantidade = request.data.get("quantidade")
        if not safra_id or not quantidade:
            return Response({"erro": "Informe a safra e a quantidade."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            nova = CompraService.reservar(int(safra_id), request.user, quantidade)
        except (ValueError, TypeError) as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ErroCompra as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TransacaoSerializer(nova).data, status=status.HTTP_201_CREATED)

    # --- Ações das partes envolvidas ---
    def _objeto_da_parte(self, pk, usuario, papel=None):
        obj = Transacao.objects.select_related("safra__produto").filter(pk=pk).first()
        if obj is None:
            from rest_framework.exceptions import NotFound

            raise NotFound("Transação não encontrada.")
        if usuario.eh_admin:
            return obj
        if papel == "comprador" and obj.comprador_id != usuario.pk:
            raise PermissionDenied("Apenas o comprador pode executar esta ação.")
        if papel == "vendedor" and obj.vendedor_id != usuario.pk:
            raise PermissionDenied("Apenas o vendedor pode executar esta ação.")
        if papel is None and usuario.pk not in (obj.comprador_id, obj.vendedor_id):
            raise PermissionDenied("Você não é parte desta transação.")
        return obj

    @action(detail=True, methods=["post"], url_path="enviar-comprovativo")
    def enviar_comprovativo(self, request, pk=None):
        """Comprador anexa o comprovativo de transferência → análise."""
        obj = self._objeto_da_parte(pk, request.user, papel="comprador")
        try:
            obj.mudar_status(
                Transacao.Statuses.ANALISE, "Comprovativo enviado pelo comprador"
            )
        except ValueError as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(TransacaoSerializer(obj).data)

    @action(detail=True, methods=["post"], url_path="confirmar-pagamento")
    def confirmar_pagamento(self, request, pk=None):
        """Admin valida o comprovativo → fundo fica retido em escrow.

        Aceita transações em análise ou ainda em aguardando_pagamento
        (pagamento direto validado pela plataforma sem upload de comprovativo).
        """
        obj = self._objeto_da_parte(pk, request.user)
        if not request.user.eh_admin:
            raise PermissionDenied("A validação de pagamentos é feita pela plataforma.")
        if obj.status == Transacao.Statuses.AGUARDANDO_PAGAMENTO:
            alvo_inicial = Transacao.Statuses.ANALISE
            try:
                obj.mudar_status(alvo_inicial, "Comprovativo recebido (validação direta)")
            except ValueError as exc:
                return Response({"erro": str(exc)}, status=status.HTTP_409_CONFLICT)
        try:
            obj.mudar_status(Transacao.Statuses.ESCROW, "Pagamento confirmado (escrow)")
        except ValueError as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(TransacaoSerializer(obj).data)

    @action(detail=True, methods=["post"], url_path="enviar")
    def enviar(self, request, pk=None):
        obj = self._objeto_da_parte(pk, request.user, papel="vendedor")
        try:
            obj.mudar_status(Transacao.Statuses.ENVIADO, "Mercadoria enviada")
        except ValueError as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(TransacaoSerializer(obj).data)

    @action(detail=True, methods=["post"], url_path="confirmar-entrega")
    def confirmar_entrega(self, request, pk=None):
        obj = self._objeto_da_parte(pk, request.user, papel="comprador")
        try:
            obj.mudar_status(Transacao.Statuses.ENTREGUE, "Entrega confirmada")
        except ValueError as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(TransacaoSerializer(obj).data)

    @action(detail=True, methods=["post"])
    def liquidar(self, request, pk=None):
        """Liberta o escrow (admin/plataforma)."""
        obj = self._objeto_da_parte(pk, request.user)
        if not request.user.eh_admin:
            raise PermissionDenied("A liquidação é feita pela plataforma.")
        try:
            obj = CompraService.liquidar(obj)
        except ErroCompra as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(TransacaoSerializer(obj).data)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        obj = self._objeto_da_parte(pk, request.user)
        try:
            obj.mudar_status(Transacao.Statuses.CANCELADO, "Cancelada pelo utilizador")
        except ValueError as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(TransacaoSerializer(obj).data)

    @action(detail=True, methods=["post"])
    def disputar(self, request, pk=None):
        obj = self._objeto_da_parte(pk, request.user)
        try:
            obj.mudar_status(Transacao.Statuses.DISPUTA,
                             (request.data.get("motivo") or "")[:255])
        except ValueError as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(TransacaoSerializer(obj).data)


class ComprovativoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comprovativo
        fields = ["id", "transacao", "caminho", "validado", "enviado_em"]
        read_only_fields = ["id", "validado", "enviado_em"]


class ComprovativoViewSet(viewsets.ModelViewSet):
    """Upload/listagem de talões — apenas as partes da transação têm acesso.

    Correção face ao Flask: a relação é por FK (não por casamento de nome de
    ficheiro), evitando exposição por colisão de caminhos.
    """

    serializer_class = ComprovativoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        from django.db.models import Q

        qs = Comprovativo.objects.select_related("transacao")
        if user.eh_admin:
            return qs
        return qs.filter(
            Q(transacao__comprador=user) | Q(transacao__vendedor=user)
        )

    def perform_create(self, serializer):
        transacao = serializer.validated_data.get("transacao")
        user = self.request.user
        if not user.eh_admin and transacao.comprador_id != user.pk:
            raise PermissionDenied("Apenas o comprador envia comprovativos.")
        serializer.save(enviado_por=user)
