from datetime import datetime

import factory

from polling.models import State
from polling.models import CANDIDATE_NONE


class StateFactory(factory.Factory):
    class Meta:
        model = State

    name = factory.Sequence(lambda n: "state-%d" % n)
    updated = factory.LazyFunction(datetime.now)
    abbv = factory.LazyAttribute(lambda obj: obj.name[-2:])
    tipping_point_rank = factory.Sequence(lambda n: int(n))
    safe_for = CANDIDATE_NONE
    safe_rank = -1
    leans = CANDIDATE_NONE
    lean_rank = -1
