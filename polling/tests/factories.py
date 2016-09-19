from django.utils import timezone
import us

import factory

from polling.models import State
from polling.models import CANDIDATE_NONE


class StateFactory(factory.DjangoModelFactory):
    class Meta:
        model = State

    name = factory.Sequence(lambda n: us.STATES[n % 51].name)
    updated = factory.LazyFunction(timezone.now)
    abbv = factory.LazyAttribute(
        lambda obj: us.states.lookup(unicode(obj.name)).abbr)
    tipping_point_rank = -1
    safe_for = CANDIDATE_NONE
    safe_rank = -1
    leans = CANDIDATE_NONE
    lean_rank = -1
