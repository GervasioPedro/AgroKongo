"""Handler central de exceções da API — erros JSON consistentes p/ o React."""
import logging

from rest_framework.views import exception_handler

logger = logging.getLogger("agrokongo.api")


def handler_api(exc, context):
    """Normaliza erros DRF para `{erro: "mensagem"}` e loga 500 não tratados."""
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data
        if isinstance(data, dict):
            if "detail" in data and len(data) == 1:
                response.data = {"erro": str(data["detail"])}
            else:
                # Validação de serializers → primeiro erro legível + campos
                resposta = {}
                for campo, valores in data.items():
                    texto = valores[0] if isinstance(valores, list) and valores else valores
                    resposta[campo] = str(texto)
                response.data = {"erro": "; ".join(resposta.values()), "campos": resposta}
        elif isinstance(data, list) and data:
            response.data = {"erro": str(data[0])}
    else:
        logger.exception("Erro não tratado na API", exc_info=exc)
    return response
