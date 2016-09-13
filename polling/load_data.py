import csv
import datetime
import os

from polling.models import State


def load_fixture(fname):
    with open(fname, 'r') as f:
        # The date of the fixture is specified by the fname
        fname_last = os.path.split(fname)[-1]
        date_str = fname_last.split(".")[0]
        print(date_str)
        import_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        tsv_file = csv.DictReader(f, delimiter='\t')
        for line in tsv_file:
            print(line['leans'])
            state, created = State.objects.get_or_create(
                name=line['name'],
                updated=import_date,
                abbv=line['abbv'],
                tipping_point_rank=int(line['tipping_point_rank'] or -1),
                safe_for=line['safe_for'],
                safe_rank=int(line['safe_rank'] or -1),
                leans=line['leans'],
                lean_rank=int(line['lean_rank'] or -1),
            )
