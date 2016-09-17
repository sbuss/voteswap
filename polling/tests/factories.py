from datetime import datetime
import us

import factory

from polling.models import State
from polling.models import CANDIDATE_NONE


class StateFactory(factory.DjangoModelFactory):
    class Meta:
        model = State

    name = factory.Sequence(lambda n: us.STATES[n])
    updated = factory.LazyFunction(datetime.now)
    abbv = factory.LazyAttribute(
        lambda obj: us.states.lookup(unicode(obj.name)).abbr)
    tipping_point_rank = -1
    safe_for = CANDIDATE_NONE
    safe_rank = -1
    leans = CANDIDATE_NONE
    lean_rank = -1
