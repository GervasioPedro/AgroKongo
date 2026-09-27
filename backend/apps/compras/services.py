"""Serviço de compra — orquestra o fluxo atómico de reserva + escrow.

Equivalente ao `compra_service.py` do Flask, reescrito com:
- `transaction.atomic()` para garantir consistência entre stock e transação;
- `select_for_update()` para evitar corrida no stock da safra;
- persistência correta do histórico de estados (bug corrigido na migração).
"""
from decimal import Decimal

from django.db import transaction

from apps.catalogo.models import Safra
from apps.compras.models import Transacao
from apps.notifications.services import notificar


class ErroCompra(Exception):
    """Erro de negócio na compra (stock insuficiente, self-deal, etc.)."""


class CompraService:
    @staticmethod
    @transaction.atomic
    def reservar(safra_id: int, comprador, quantidade) -> Transacao:
        quantidade = Decimal(str(quantidade))

        if quantidade <= 0:
            raise ErroCompra("A quantidade deve ser maior que zero.")
        if comprador.eh_produtor and safra_id and getattr(
            comprador, "safras", None
        ) and Safra.objects.filter(pk=safra_id, produtor=comprador).exists():
            raise ErroCompra("Não é possível comprar a própria safra.")

        safra = (
            Safra.objects.select_for_update()
            .select_related("produto", "produtor")
            .filter(pk=safra_id)
            .first()
        )
        if safra is None:
            raise ErroCompra("Safra não encontrada.")
        if safra.status != Safra.Statuses.DISPONIVEL:
            raise ErroCompra("Esta safra não está disponível para venda.")
        if safra.quantidade_disponivel < quantidade:
            raise ErroCompra(
                f"Stock insuficiente. Disponível: {safra.quantidade_disponivel} "
                f"{safra.unidade}."
            )

        valor_total = (quantidade * safra.preco_por_unidade).quantize(Decimal("0.01"))

        transacao = Transacao(
            fatura_ref=Transacao.gerar_fatura_ref(),
            safra=safra,
            comprador=comprador,
            vendedor=safra.produtor,
            quantidade_comprada=quantidade,
            valor_total_pago=valor_total,
        )
        transacao.calcular_split()
        transacao.save()
        transacao.mudar_status(
            Transacao.Statuses.AGUARDANDO_PAGAMENTO, "Reserva criada pelo comprador"
        )

        # Desconta o stock e marca como esgotada se necessário
        safra.quantidade_disponivel -= quantidade
        if safra.quantidade_disponivel == 0:
            safra.status = Safra.Statuses.ESGOTADA
        safra.save(update_fields=["quantidade_disponivel", "status", "atualizado_em"])

        notificar(comprador, f"Reserva {transacao.fatura_ref} efetuada com sucesso.",
                  link=f"/dashboard/compras/{transacao.pk}")
        notificar(safra.produtor, f"Nova reserva na sua safra de {safra.produto.nome}.",
                  link=f"/dashboard/vendas/{transacao.pk}")

        return transacao

    @staticmethod
    @transaction.atomic
    def liquidar(transacao: Transacao) -> Transacao:
        """Liberta o escrow para o vendedor após entrega confirmada."""
        if transacao.status != Transacao.Statuses.ENTREGUE:
            raise ErroCompra(
                "Só é possível liquidar transações com mercadoria entregue."
            )
        vendedor = transacao.vendedor
        vendedor.saldo_disponivel = Decimal(vendedor.saldo_disponivel) + Decimal(
            transacao.valor_liquido_vendedor
        )
        vendedor.vendas_concluidas += 1
        vendedor.save(update_fields=["saldo_disponivel", "vendas_concluidas",
                                     "atualizado_em"])
        transacao.mudar_status(Transacao.Statuses.FINALIZADO, "Escrow liquidado")
        notificar(vendedor,
                  f"Pagamento de {transacao.valor_liquido_vendedor} Kz libertado "
                  f"para o seu saldo ({transacao.fatura_ref}).",
                  link=f"/dashboard/vendas/{transacao.pk}")
        return transacao
