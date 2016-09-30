import os

from django.core.management.base import BaseCommand
from polling.load_data import load_fixture


class Command(BaseCommand):
    help = 'Load all polling fixtures into the database'

    def handle(self, *args, **options):
        data_dir = 'polling/data'
        for fname in os.listdir(data_dir):
            path = os.path.join(data_dir, fname)
            if not os.path.isfile(path):
                continue
            load_fixture(path)
