from django.test import TestCase
from django.utils import timezone
from mock import MagicMock
from mock import call
from mock import patch

from users.models import PairProposal
from users.views import _send_swap_proposal_email
from users.views import _send_reject_swap_email
from users.views import _send_confirm_swap_email
from users.tests.factories import UserFactory
from polling.models import CANDIDATE_CLINTON
from polling.models import CANDIDATE_JOHNSON
from polling.models import CANDIDATE_STEIN
from polling.tests.factories import StateFactory


class TestEmailBase(TestCase):
    def _iter_email_message_instances(self, *args, **kwargs):
        while True:
            m = MagicMock()
            self.mock_email_messages.append(m)
            yield m

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
            to_profile=self.to_user.profile,
            date_rejected=timezone.now())
        self.mock_email_messages = []
        self.email_patcher = patch(
            'users.views.EmailMessage',
            side_effect=self._iter_email_message_instances())
        self.mock_email_message_class = self.email_patcher.start()

    def tearDown(self):
        self.email_patcher.stop()

    def test_proposal_email(self):
        _send_swap_proposal_email(self.from_user, self.proposal)
        self.assertEqual(len(self.mock_email_messages), 1)
        self.mock_email_message_class.assert_called_with(
            sender=u'noreply@voteswap.us',
            to=unicode(self.to_user.email),
            subject=u'New VoteSwap with %s' % self.from_user.profile.fb_name)
        [email_message] = self.mock_email_messages
        for attr in ['body', 'html']:
            contents = getattr(email_message, attr)
            contents = contents.replace('\n', ' ')
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
        email_message.send.assert_called_once()

    def test_proposal_email_kingmaker(self):
        # Switch the from/to so the Johnson voter in the swing state gets
        # the kingmaker email
        self.proposal.from_profile = self.to_user.profile
        self.proposal.to_profile = self.from_user.profile
        _send_swap_proposal_email(self.from_user, self.proposal)
        [email_message] = self.mock_email_messages
        self.assertIn(
            "Voting for Johnson in %s" % self.from_user.profile.state,
            email_message.body)
        self.assertIn(
            "Voting for Johnson in %s" % self.from_user.profile.state,
            email_message.html)

    def test_proposal_email_kingmaker_stein(self):
        # Same as above, but with stein
        self.proposal.from_profile = self.to_user.profile
        self.proposal.to_profile = self.from_user.profile
        self.proposal.to_profile.preferred_candidate = CANDIDATE_STEIN
        self.proposal.to_profile.save()
        _send_swap_proposal_email(self.from_user, self.proposal)
        [email_message] = self.mock_email_messages
        self.assertIn(
            "Voting for Stein in %s" % self.from_user.profile.state,
            email_message.body)
        self.assertIn(
            "Voting for Stein in %s" % self.from_user.profile.state,
            email_message.html)

    def test_reject_email(self):
        _send_reject_swap_email(self.to_user, self.proposal)
        self.assertEqual(len(self.mock_email_messages), 1)
        self.mock_email_message_class.assert_called_with(
            sender=u'noreply@voteswap.us',
            to=unicode(self.from_user.email),
            subject=(u'%s rejected your VoteSwap' %
                     self.to_user.profile.fb_name))
        [email_message] = self.mock_email_messages
        for attr in ['body', 'html']:
            contents = getattr(email_message, attr)
            contents = contents.replace('\n', ' ')
            from_profile = self.from_user.profile
            to_profile = self.to_user.profile
            self.assertIn("Hi, %s" % from_profile.fb_name, contents)
            self.assertIn(
                ("%s has rejected" % to_profile.fb_name), contents)
            self.assertIn("Please come back to", contents)
            self.assertIn("https://voteswap.us/swap", contents)
        email_message.send.assert_called_once()

    def test_reject_pending_matches(self):
        extra_user = UserFactory.create()
        PairProposal.objects.create(
            from_profile=self.from_user.profile,
            to_profile=extra_user.profile)
        _send_reject_swap_email(self.to_user, self.proposal)
        [email_message] = self.mock_email_messages
        for attr in ['body', 'html']:
            contents = getattr(email_message, attr)
            contents = contents.replace('\n', ' ')
            self.assertIn("You still have 1 pending swaps", contents)
            self.assertIn("https://voteswap.us/swap", contents)

    def test_reject_one_good_potential_match(self):
        # Add a new friend that's a good potential match
        extra_state = StateFactory.create(safe_rank=2)
        self.from_user.profile.friends.add(UserFactory.create(
            profile__state=extra_state.name,
            profile__preferred_candidate=CANDIDATE_CLINTON).profile)
        _send_reject_swap_email(self.to_user, self.proposal)
        [email_message] = self.mock_email_messages
        for attr in ['body', 'html']:
            contents = getattr(email_message, attr)
            contents = contents.replace('\n', ' ')
            self.assertIn("You have 1 good potential match", contents)
            self.assertIn("https://voteswap.us/swap", contents)

    def test_reject_two_good_potential_match(self):
        # Add a new friend that's a good potential match
        extra_state = StateFactory.create(safe_rank=2)
        self.from_user.profile.friends.add(UserFactory.create(
            profile__state=extra_state.name,
            profile__preferred_candidate=CANDIDATE_CLINTON).profile)
        self.from_user.profile.friends.add(UserFactory.create(
            profile__state=extra_state.name,
            profile__preferred_candidate=CANDIDATE_CLINTON).profile)
        _send_reject_swap_email(self.to_user, self.proposal)
        [email_message] = self.mock_email_messages
        for attr in ['body', 'html']:
            contents = getattr(email_message, attr)
            contents = contents.replace('\n', ' ')
            self.assertIn("You have 2 good potential matches", contents)
            self.assertIn("https://voteswap.us/swap", contents)

    def test_confirm_email(self):
        _send_confirm_swap_email(self.to_user, self.proposal)
        self.assertEqual(len(self.mock_email_messages), 2)
        calls = [
            call(sender=u'noreply@voteswap.us',
                 to=unicode(self.to_user.email),
                 reply_to=unicode(self.from_user.email),
                 subject=(
                     'Your VoteSwap with %s is confirmed!' %
                     self.from_user.profile.fb_name)),
            call(sender=u'noreply@voteswap.us',
                 to=unicode(self.from_user.email),
                 reply_to=unicode(self.to_user.email),
                 subject=(
                     'Your VoteSwap with %s is confirmed!' %
                     self.to_user.profile.fb_name)),
        ]
        self.mock_email_message_class.assert_has_calls(calls)

        for (from_profile, to_profile) in [
                (self.proposal.to_profile, self.proposal.from_profile),
                (self.proposal.from_profile, self.proposal.to_profile)]:
            email_message = self.mock_email_messages.pop(0)
            for attr in ['body', 'html']:
                contents = getattr(email_message, attr)
                contents = contents.replace('\n', ' ')
                self.assertIn(
                    "Congratulations, %s" % to_profile.fb_name,
                    contents)
                self.assertIn(
                    ("You are confirmed to swap your vote with %s" %
                     from_profile.fb_name),
                    contents)
                self.assertIn(
                    ("They're a %s voter in %s" %
                     (from_profile.preferred_candidate,
                      from_profile.state)),
                    contents)
                self.assertIn("Tuesday, November 8th", contents)
                self.assertIn(
                    ("to send %s an email" % from_profile.fb_name),
                    contents)
                self.assertIn(
                    "https://facebook.com/messages/%s" % from_profile.fb_id,
                    contents)
            email_message.send.assert_called_once()
