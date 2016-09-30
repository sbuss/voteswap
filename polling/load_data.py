import csv
import os
from django.utils import timezone

from polling.models import State


def _val(line, key):
    return int(line.get(key, None) or -1)


def load_fixture(fname):
    with open(fname, 'r') as f:
        # The date of the fixture is specified by the fname
        fname_last = os.path.split(fname)[-1]
        date_str = fname_last.split(".")[0]
        print(date_str)
        import_date = timezone.datetime.strptime(date_str, '%Y-%m-%d')
        tsv_file = csv.DictReader(f, delimiter='\t')
        for line in tsv_file:
            state, created = State.all_objects.get_or_create(
                name=line['name'],
                updated=import_date,
                abbv=line['abbv'],
                tipping_point_rank=_val(line, 'tipping_point_rank'),
                safe_for=line['safe_for'],
                safe_rank=_val(line, 'safe_rank'),
                leans=line['leans'],
                lean_rank=_val(line, 'lean_rank'),
            )
