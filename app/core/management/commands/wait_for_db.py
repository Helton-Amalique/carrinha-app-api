"""Comando django para a espera pela base de dados"""
import time
from psycopg2 import OperationalError as Psycopg2OpError
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django comando para espera pela DB"""

    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write('Esperando pela base de dados....')
        db_up = False
        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2OpError, OperationalError):
                self.stdout.write(
                    'Database nao disponivel, aguarde 1 segund...'
                )
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Base de dados desponivel!'))
