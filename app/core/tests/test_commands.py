"""
Test custom Django management commands.
"""

from unittest.mock import patch

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase
from psycopg2 import OperationalError as Psycopg2Error


# Mockando o valor da função de comando
@patch("core.management.commands.wait_for_db.Command.check")
class CommandsTests(SimpleTestCase):
    """Test commands."""

    def test_wait_for_db_ready(self, patched_check):
        """Test  waiting for database if database ready."""
        # Passo o valor de true para quando essa função for chamada
        patched_check.return_value = True

        call_command("wait_for_db")

        # Verifica se o valor de database chamado é o default
        patched_check.assert_called_once_with(databases=["default"])

    @patch("time.sleep")
    def test_wait_for_db_delay(self, patched_sleep, patched_check):
        """Test waiting for database when getting OperationalError"""
        # O side effect simula certa situações no caso abaixo ele tá simulando
        # Que o error Psycopg2Error é chamado 2 vezes, depois o
        # OperationalError é chamado 3 vezes e depois termina como True
        patched_check.side_effect = (
            [Psycopg2Error] * 2 + [OperationalError] * 3 + [True]
        )

        call_command("wait_for_db")
        self.assertEqual(patched_check.call_count, 6)
        patched_check.assert_called_with(databases=["default"])
