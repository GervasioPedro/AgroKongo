from rest_framework import serializers, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.geo.models import Municipio, Provincia


class ProvinciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provincia
        fields = ["id", "nome", "codigo", "area_km2", "populacao_2024"]


class MunicipioSerializer(serializers.ModelSerializer):
    provincia_nome = serializers.CharField(source="provincia.nome", read_only=True)

    class Meta:
        model = Municipio
        fields = ["id", "nome", "provincia", "provincia_nome"]


class ProvinciaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Provincia.objects.all()
    serializer_class = ProvinciaSerializer
    permission_classes = [AllowAny]
    search_fields = ["nome"]


class MunicipioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Municipio.objects.select_related("provincia").all()
    serializer_class = MunicipioSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["provincia"]
    search_fields = ["nome"]
