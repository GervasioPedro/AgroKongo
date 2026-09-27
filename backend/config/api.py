"""Router raiz da API REST do AgroKongo (DRF)."""
from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.accounts.views import AuthView, PedidoResetSenhaView, UsuarioViewSet
from apps.catalogo.views import ProdutoViewSet, SafraViewSet
from apps.chat.views import MensagemViewSet
from apps.compras.views import ComprovativoViewSet, TransacaoViewSet
from apps.geo.views import MunicipioViewSet, ProvinciaViewSet
from apps.notifications.views import NotificacaoViewSet

router = SimpleRouter(trailing_slash=False)
router.register("utilizadores", UsuarioViewSet, basename="utilizador")
router.register("produtos", ProdutoViewSet, basename="produto")
router.register("safras", SafraViewSet, basename="safra")
router.register("transacoes", TransacaoViewSet, basename="transacao")
router.register("comprovativos", ComprovativoViewSet, basename="comprovativo")
router.register("notificacoes", NotificacaoViewSet, basename="notificacao")
router.register("mensagens", MensagemViewSet, basename="mensagem")
router.register("provincias", ProvinciaViewSet, basename="provincia")
router.register("municipios", MunicipioViewSet, basename="municipio")


api_urlpatterns = router.urls + [
    path("auth", AuthView.as_view(), name="auth"),
    path("auth/pedido-reset", PedidoResetSenhaView.as_view(),
         name="auth-pedido-reset"),
]
