from django.contrib.auth import authenticate
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.auth import TokenAuthentication, criar_sessao, encerrar_sessao
from apps.accounts.models import Usuario
from apps.accounts.permissions import IsAdmin


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            "id", "nome", "telemovel", "email", "tipo", "nif", "iban",
            "rating_vendedor", "vendas_concluidas", "foto_perfil",
            "perfil_completo", "conta_validada", "provincia", "municipio",
            "criado_em",
        ]
        read_only_fields = [
            "id", "rating_vendedor", "vendas_concluidas", "conta_validada",
            "criado_em",
        ]


class RegistoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=100)
    telemovel = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True)
    senha = serializers.CharField(write_only=True, min_length=8, max_length=128)
    confirmar_senha = serializers.CharField(write_only=True)
    tipo = serializers.ChoiceField(
        choices=[Usuario.Tipos.PRODUTOR, Usuario.Tipos.COMPRADOR],
        required=False, default=Usuario.Tipos.COMPRADOR,
    )

    def validate(self, attrs):
        if attrs["senha"] != attrs.pop("confirmar_senha"):
            raise serializers.ValidationError({"confirmar_senha": "As senhas não coincidem."})
        return attrs


class LoginSerializer(serializers.Serializer):
    telemovel = serializers.CharField(max_length=20)
    senha = serializers.CharField(write_only=True)


class UsuarioViewSet(viewsets.ModelViewSet):
    """Gestão de utilizadores (lista/detalhe para admin; self para qualquer um)."""

    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["tipo", "conta_validada", "provincia"]
    search_fields = ["nome", "telemovel", "email"]

    def get_permissions(self):
        if self.action in ("list", "destroy"):
            return [IsAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.eh_admin:
            return Usuario.objects.all()
        if self.action == "retrieve":
            # Qualquer autenticado pode ver perfil público básico
            return Usuario.objects.all()
        return Usuario.objects.filter(pk=user.pk)

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        return Response(UsuarioSerializer(request.user).data)

    @action(detail=False, methods=["patch", "put"], url_path="me")
    def atualizar_me(self, request):
        """PATCH /api/v1/utilizadores/me — edição do próprio perfil
        (usado pela página completar-perfil do React)."""
        dados = dict(request.data)
        # Nunca permitir auto-elevação/auto-validação pelo próprio utilizador
        for campo_protegido in ("tipo", "conta_validada", "rating_vendedor",
                                "vendas_concluidas", "senha"):
            dados.pop(campo_protegido, None)
        serializer = UsuarioSerializer(
            request.user, data=dados, partial=request.method == "PATCH"
        )
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        if not usuario.perfil_completo and all(
            [usuario.nif, usuario.iban, usuario.provincia_id, usuario.municipio_id]
        ):
            usuario.perfil_completo = True
            usuario.save(update_fields=["perfil_completo"])
        return Response(UsuarioSerializer(usuario).data)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class AuthView(APIView):
    """POST /api/v1/auth  {acao: registo|login|logout, ...}

    Mantém a semântica das rotas antigas (`/auth/registo`, `/auth/login`)
    num único endpoint REST orientado ao React.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        acao = request.data.get("acao", "login")
        if acao == "registo":
            return self._registo(request)
        if acao == "login":
            return self._login(request)
        if acao == "logout":
            return self._logout(request)
        return Response({"erro": "Ação de autenticação inválida."},
                        status=status.HTTP_400_BAD_REQUEST)

    def _registo(self, request):
        ser = RegistoSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        dados = ser.validated_data
        try:
            user = Usuario.objects.create_user(
                telemovel=dados["telemovel"],
                nome=dados["nome"],
                senha=dados["senha"],
                email=dados.get("email") or "",
                tipo=dados.get("tipo", Usuario.Tipos.COMPRADOR),
            )
        except ValueError as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        token = criar_sessao(user, request)
        return Response({
            "token": token,
            "utilizador": UsuarioSerializer(user).data,
        }, status=status.HTTP_201_CREATED)

    def _login(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = authenticate(
            request,
            telemovel=ser.validated_data["telemovel"],
            password=ser.validated_data["senha"],
        )
        if user is None:
            return Response({"erro": "Credenciais inválidas."},
                            status=status.HTTP_401_UNAUTHORIZED)
        token = criar_sessao(user, request)
        return Response({
            "token": token,
            "utilizador": UsuarioSerializer(user).data,
        })

    def _logout(self, request):
        # Autentica o header Bearer só para saber qual sessão fechar
        auth = TokenAuthentication()
        try:
            auth.authenticate(request)
        except Exception:
            return Response({"mensagem": "Sem sessão ativa."}, status=status.HTTP_200_OK)
        encerrar_sessao(request)
        return Response({"mensagem": "Sessão terminada."})


class PedidoResetSenhaView(APIView):
    """Regista o pedido de reset — envio por SMS/email fica em tasks assíncronas."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        from apps.notifications.services import pedir_reset_senha

        identificador = request.data.get("telemovel") or request.data.get("email")
        if not identificador:
            return Response({"erro": "Indique o telemóvel ou email da conta."},
                            status=status.HTTP_400_BAD_REQUEST)
        criado = pedir_reset_senha(identificador)
        # Nunca revela se a conta existe (anti-enumeration)
        return Response({
            "mensagem": "Se a conta existir, receberá instruções de recuperação.",
            "pedido_registado": criado,
        })
