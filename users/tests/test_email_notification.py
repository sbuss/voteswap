from django.core import mail as testmail
from django.test import TestCase
from django.test import override_settings
from django.utils import timezone

from users.models import PairProposal
from users.views import _send_swap_proposal_email
from users.views import _send_reject_swap_email
from users.views import _send_confirm_swap_email
from users.tests.factories import UserFactory
from polling.models import CANDIDATE_CLINTON
from polling.models import CANDIDATE_JOHNSON
from polling.models import CANDIDATE_STEIN
from polling.tests.factories import StateFactory


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
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
            to_profile=self.to_user.profile,
            date_rejected=timezone.now())

    def test_proposal_email(self):
        self.assertEqual(len(testmail.outbox), 0)
        _send_swap_proposal_email(self.from_user, self.proposal)
        self.assertEqual(len(testmail.outbox), 1)
        [message] = testmail.outbox
        self.assertEqual(message.from_email, u'noreply@email.voteswap.us')
        self.assertEqual(message.recipients(), [self.to_user.email])
        self.assertEqual(
            message.subject,
            u'New VoteSwap with %s' % self.from_user.profile.fb_name)
        self.assertEqual(len(message.alternatives), 1)
        bodies = [message.body, message.alternatives[0][0]]
        for contents in bodies:
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

    def test_proposal_email_kingmaker(self):
        # Switch the from/to so the Johnson voter in the swing state gets
        # the kingmaker email
        self.proposal.from_profile = self.to_user.profile
        self.proposal.to_profile = self.from_user.profile
        _send_swap_proposal_email(self.from_user, self.proposal)
        [email_message] = testmail.outbox
        self.assertIn(
            "Voting for Johnson in %s" % self.from_user.profile.state,
            email_message.body)
        self.assertIn(
            "Voting for Johnson in %s" % self.from_user.profile.state,
            email_message.alternatives[0][0])

    def test_proposal_email_kingmaker_stein(self):
        # Same as above, but with stein
        self.proposal.from_profile = self.to_user.profile
        self.proposal.to_profile = self.from_user.profile
        self.proposal.to_profile.preferred_candidate = CANDIDATE_STEIN
        self.proposal.to_profile.save()
        _send_swap_proposal_email(self.from_user, self.proposal)
        [email_message] = testmail.outbox
        self.assertIn(
            "Voting for Stein in %s" % self.from_user.profile.state,
            email_message.body)
        self.assertIn(
            "Voting for Stein in %s" % self.from_user.profile.state,
            email_message.alternatives[0][0])

    def test_reject_email(self):
        self.assertEqual(len(testmail.outbox), 0)
        _send_reject_swap_email(self.to_user, self.proposal)
        self.assertEqual(len(testmail.outbox), 1)
        [message] = testmail.outbox
        self.assertEqual(message.from_email, u'noreply@email.voteswap.us')
        self.assertEqual(message.recipients(), [self.from_user.email])
        self.assertEqual(
            message.subject,
            u'%s rejected your VoteSwap' % self.to_user.profile.fb_name)
        bodies = [message.body, message.alternatives[0][0]]
        for contents in bodies:
            contents = contents.replace('\n', ' ')
            from_profile = self.from_user.profile
            to_profile = self.to_user.profile
            self.assertIn("Hi, %s" % from_profile.fb_name, contents)
            self.assertIn(
                ("%s has rejected" % to_profile.fb_name), contents)
            self.assertIn("Please come back to", contents)
            self.assertIn("https://voteswap.us/swap", contents)

    def test_reject_pending_matches(self):
        extra_user = UserFactory.create()
        PairProposal.objects.create(
            from_profile=self.from_user.profile,
            to_profile=extra_user.profile)
        _send_reject_swap_email(self.to_user, self.proposal)
        [message] = testmail.outbox
        bodies = [message.body, message.alternatives[0][0]]
        for contents in bodies:
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
        [message] = testmail.outbox
        bodies = [message.body, message.alternatives[0][0]]
        for contents in bodies:
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
        [message] = testmail.outbox
        bodies = [message.body, message.alternatives[0][0]]
        for contents in bodies:
            contents = contents.replace('\n', ' ')
            self.assertIn("You have 2 good potential matches", contents)
            self.assertIn("https://voteswap.us/swap", contents)

    def test_confirm_email(self):
        self.assertEqual(len(testmail.outbox), 0)
        _send_confirm_swap_email(self.to_user, self.proposal)
        self.assertEqual(len(testmail.outbox), 2)
        for (from_profile, to_profile) in [
                (self.proposal.to_profile, self.proposal.from_profile),
                (self.proposal.from_profile, self.proposal.to_profile)]:
            message = testmail.outbox.pop(0)
            self.assertEqual(message.from_email, u'noreply@email.voteswap.us')
            self.assertEqual(message.recipients(), [from_profile.user.email])
            self.assertEqual(message.reply_to, [to_profile.user.email])
            self.assertEqual(
                message.subject,
                ('Your VoteSwap with %s is confirmed!' %
                 to_profile.fb_name))
            bodies = [message.body, message.alternatives[0][0]]
            for contents in bodies:
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
