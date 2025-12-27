"""
Inicialização do pacote de testes
Configuração comum para todos os testes do sistema AgroKongo.
"""
import os
import tempfile
import sqlite3
from unittest import TestCase


class BaseTestCase(TestCase):
    """Classe base para todos os testes com setup/teardown comum"""

    def setUp(self):
        """Configuração antes de cada teste"""
        # Criar banco de dados temporário para testes
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.test_db_url = f"sqlite:///{self.db_path}"

        # Configurar ambiente de teste
        os.environ['FLASK_ENV'] = 'testing'

    def tearDown(self):
        """Limpeza após cada teste"""
        os.close(self.db_fd)
        os.unlink(self.db_path)