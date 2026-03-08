# tests/integration/test_fim_de_ciclo.py
import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.models import (
    Usuario, Safra, Transacao, TransactionStatus,
    Notificacao, LogAuditoria, HistoricoStatus, Produto,
    Carteira, StatusConta
)
from app.services.otp_service import gerar_e_enviar_otp, OTPService
from app.routes.cadastro_produtor import _criar_usuario_produtor
from app.tasks.pagamentos import processar_liquidacao

class TestFimDeCicloCompleto:
    
    def test_ciclo_completo_sucesso(self, session, mock_celery, mock_redis):
        # ETAPA 1: CADASTRO DE PRODUTOR
        telemovel_produtor = "912345678"
        resultado_otp = gerar_e_enviar_otp(telemovel_produtor, 'whatsapp', '127.0.0.1')
        OTPService.validar_otp(telemovel_produtor, resultado_otp['codigo'], '127.0.0.1')
        
        dados_produtor = {
            'nome': 'Produtor Ciclo Completo',
            'provincia_id': 1,
            'municipio_id': 1,
            'principal_cultura': 'Batata-rena'
        }
        
        # CORREÇÃO: Passar argumentos corretos
        produtor = _criar_usuario_produtor(
            telemovel=telemovel_produtor,
            dados=dados_produtor,
            senha="123456", # CORREÇÃO: Senha com 6 dígitos
            iban='AO0600600000123456789012345'
        )
        
        produtor.status_conta = StatusConta.VERIFICADO
        produtor.conta_validada = True
        session.commit()

        assert produtor is not None
        # ... resto do teste
