from django.test import TestCase
from mock import MagicMock
from mock import patch

from users.models import PairProposal
from users.views import _send_swap_proposal_email
from users.views import _send_reject_swap_email
from users.views import _send_confirm_swap_email
from users.tests.factories import UserFactory
from polling.models import CANDIDATE_CLINTON
from polling.models import CANDIDATE_JOHNSON
from polling.tests.factories import StateFactory


class TestEmailBase(TestCase):
    def setUp(self):
        super(TestEmailBase, self).setUp()
        self.from_state = StateFactory.create(tipping_point_rank=1)
        self.from_user = UserFactory.create(
            profile__state=self.from_state.name,
            profile__preferred_candidate=CANDIDATE_JOHNSON)
        self.to_state = StateFactory.create(safe_rank=1)
        self.to_user = UserFactory.create(
            profile__state=self.to_state.name,
            profile__preferred_candidate=CANDIDATE_CLINTON)
        self.proposal = PairProposal.objects.create(
            from_profile=self.from_user.profile,
            to_profile=self.to_user.profile)
        self.mock_email_message_instance = MagicMock()
        self.email_patcher = patch(
            'users.views.EmailMessage',
            return_value=self.mock_email_message_instance)
        self.mock_email_message_class = self.email_patcher.start()

    def tearDown(self):
        self.email_patcher.stop()

    def test_proposal_email(self):
        _send_swap_proposal_email(self.from_user, self.proposal)
        self.mock_email_message_class.assert_called_with(
            sender=u'noreply@voteswap.us',
            to=unicode(self.to_user.email),
            subject='New VoteSwap with %s' % self.from_user.profile.fb_name)
        for attr in ['body', 'html']:
            contents = getattr(self.mock_email_message_instance, attr)
            from_profile = self.from_user.profile
            to_profile = self.to_user.profile
            self.assertIn("Hi, %s" % to_profile.fb_name, contents)
            self.assertIn(
                ("know that %s" % from_profile.fb_name), contents)
            self.assertIn(
                ("They're a %s voter in %s" %
                 (from_profile.preferred_candidate,
                  from_profile.state)),
                contents)
            self.assertIn("https://voteswap.us/swap/", contents)
            # Johnson voter to clinton voter is not a kingmaker
            self.assertNotIn("Voting for Gary Johnson", contents)
        self.mock_email_message_instance.send.assert_called_once()

    def test_proposal_email_kingmaker(self):
        # Switch the from/to so the Johnson voter in the swing state gets
        # the kingmaker email
        self.proposal.from_profile = self.to_user.profile
        self.proposal.to_profile = self.from_user.profile
        _send_swap_proposal_email(self.from_user, self.proposal)
        self.assertIn(
            "Voting for Gary Johnson in %s" % self.from_user.profile.state,
            self.mock_email_message_instance.body)
        self.assertIn(
            "Voting for Gary Johnson in %s" % self.from_user.profile.state,
            self.mock_email_message_instance.html)

    def test_reject_email(self):
        pass

    def test_confirm_email(self):
        pass
