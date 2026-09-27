from rest_framework import serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsProdutor, KYCAprovado
from apps.catalogo.models import Produto, Safra


class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = ["id", "nome", "categoria"]


class SafraSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source="produto.nome", read_only=True)
    categoria = serializers.CharField(source="produto.categoria", read_only=True)
    produtor_nome = serializers.CharField(source="produtor.nome", read_only=True)
    produtor_rating = serializers.DecimalField(
        source="produtor.rating_vendedor", max_digits=3, decimal_places=2,
        read_only=True,
    )
    localizacao = serializers.SerializerMethodField()
    imagem_url = serializers.CharField(read_only=True)

    class Meta:
        model = Safra
        fields = [
            "id", "produto", "produto_nome", "categoria", "quantidade_disponivel",
            "unidade", "preco_por_unidade", "status", "imagem", "imagem_url",
            "observacoes", "produtor", "produtor_nome", "produtor_rating",
            "localizacao", "valor_estimado", "criado_em",
        ]
        read_only_fields = ["id", "status", "produtor", "criado_em"]

    def get_localizacao(self, obj):
        if obj.produtor.municipio_id and obj.produtor.provincia_id:
            return f"{obj.produtor.municipio.nome}, {obj.produtor.provincia.nome}"
        return "Localização N/D"


class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            from rest_framework.permissions import AllowAny

            return [AllowAny()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        # Só administradores gerem o catálogo de produtos
        if not request.user.eh_admin:
            return Response({"erro": "Apenas administradores gerem produtos."},
                            status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not request.user.eh_admin:
            return Response({"erro": "Apenas administradores gerem produtos."},
                            status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    destroy = update


class SafraViewSet(viewsets.ModelViewSet):
    """Vitrine pública de safras + gestão das próprias safras pelo produtor."""

    serializer_class = SafraSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            from rest_framework.permissions import AllowAny

            return [AllowAny()]
        return [IsAuthenticated(), IsProdutor(), KYCAprovado()]

    def get_queryset(self):
        qs = Safra.objects.select_related(
            "produto", "produtor", "produtor__municipio", "produtor__provincia"
        )
        params = self.request.query_params
        acao = self.action

        usuario = getattr(self.request.user, "tipo", None)
        eh_admin = bool(getattr(self.request.user, "eh_admin", False))

        # ?produtor=meu → safras do produtor autenticado (dashboard React)
        filtro_produtor = params.get("produtor")
        if filtro_produtor == "meu":
            filtro_produtor = str(getattr(self.request.user, "pk", "") or "")

        if acao == "list":
            if not eh_admin:
                if filtro_produtor and str(filtro_produtor) == str(
                    getattr(self.request.user, "pk", "")
                ):
                    # Produtor vê as suas próprias safras em qualquer estado
                    pass
                else:
                    qs = qs.filter(status=Safra.Statuses.DISPONIVEL)
            if filtro_produtor:
                qs = qs.filter(produtor_id=filtro_produtor)
        else:
            if filtro_produtor:
                qs = qs.filter(produtor_id=filtro_produtor)

        # Filtro por PROVÍNCIA aceita nome OU id (corrige o bug do Flask)
        provincia = params.get("provincia")
        if provincia:
            if str(provincia).isdigit():
                qs = qs.filter(produtor__provincia_id=int(provincia))
            else:
                qs = qs.filter(produtor__provincia__nome__iexact=provincia)

        if params.get("produto"):
            qs = qs.filter(produto_id=params["produto"])
        if params.get("categoria"):
            qs = qs.filter(produto__categoria__iexact=params["categoria"])
        if params.get("busca"):
            busca = params["busca"]
            qs = qs.filter(produto__nome__icontains=busca)
        return qs

    def perform_create(self, serializer):
        serializer.save(produtor=self.request.user)

    def perform_update(self, serializer):
        self._checar_donos(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._checar_donos(instance)
        instance.delete()

    def _checar_donos(self, safra):
        user = self.request.user
        if safra.produtor_id != user.pk and not user.eh_admin:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Esta safra não pertence ao utilizador.")
