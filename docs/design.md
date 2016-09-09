# Landing page

Users who visit the site will be shown a current estimate of the likelihood of
each candidate winning (a la 538's election prediction bar) with the vote pledges
and, below that, the probabilities of wins without pledges (just 538's bar).

Below that, probabilities broken down by swing states will be shown (top 10 states?)
Include a link to the full state list (totals both with and without swaps)

If a user has allowed geolocation, the stats from their state will be shown, eg:
4321 people pledged to vote for Candidate X in exchange for Candidate Y in State Z

At the bottom have a big action button saying "Swap my vote!"

# User sign up

## Fake Users

A concern in user registration is the likelihood of fake users and fraud. This
can be mitigated by requiring a user to user their phone number to respond to
a security challenge.

Users will be wary to link their vote to their phone due to privacy concerns.

* Phone numbers shall be stored as hashes with a private salt.
* The salt should be stored separate from source (env var?)
  * How to handle a leak? Privacy is important

## Flow

1. Where do you live (geolocation api required, allow override, flag non-matches)
2. Pick your candidates in order of preference, regardless of who you *think* will win
    a. Inform user that candidates are shown in random order
    b. Show candidates in random order, click-and-drag to reorder
3. How likely are you to follow through on your pledge if [Candidate #2] is in the lead? [0-5]
4. How likely are you to follow through on your pledge is [Candidate #3] is in the lead? [0-5]
5. How likely do you think other people are to follow through on their pledge? [0-5]
6. Your phone number 
    a. Q: Why do you need this?
       A: We want to minimize the risk of fraud, and the simplest way of doing
       that is verifying that every user has a phone which can receive text
       messages. It's not always true that a person only has one phone, but it's
       true enough of the time that our results won't be too skewed.

       Q: I don't want my vote to be traced back to me
       A: We will do our best to ensure that your data stays safe. Your phone
       number will be encrypted with SHA256 encryption with a private salt
       before being stored. This approach to encryption has the best chance of
       preventing data from being accidentally disclosed. We will delete the
       encrypted phone numbers as soon as election day has ended. All data will
       be stored on Google's cloud, which we believe provides the most secure
       cloud database.

       Q: What will you use my phone number for?
       A: We will use your phone number now to send you a text which will be
       used to verify that you are a real person and you are not creating a
       bunch of fake accounts to skew the election in one direction. We will
       use your phone number again on election day to remind you of your vote
       swap pledge and to verify that you voted like you pledge. Additionally,
       you can use your phone number to log in at any time to update or delete
       your pledge.
7. Show user a matching vote swap pledge from another state and how likely that
person thinks they are to vote like they pledged. This can show a real person
is serious about their pledge and increase the likelihood of both parties
participating. 
    a. TODO Text the matching pledge with the same info?
8. Ask user for permission to create a vote swap pledge:
    "By clicking "I pledge to swap my vote" your pledge will be added to a
    public pool of "vote swap pledges". Only your state and top two candidate
    choices will be revealed. Your phone number will be encrypted and stored 
    only so you can confirm your vote swap on election day.

    Q: Is this legal?
    A: Yes! All of these are legal:
       * Pledging to swap your vote (link to 9th circuit ruling)
       * Tweeting or posting on facebook (or elsewhere) that you will vote, or have voted for a particular candidate
       * Encouraging others to vote for a particular candidate
    
    Q: What *is* illegal, then?
    A: Please remember that the following are illegal:
       * Exchanging your vote for money
       * Coercing someone to vote through threats
       * Taking a picture or video of your ballot (most jurisdictions [link to map])
       * Taking a picture or video in, of, or in some cases near, your polling place (most jurisdictions [link to map])

    You will be pledging to vote for [Candidate #2] in [your state], and you are
    matched with a pledge to vote for [Candidate #1] in [other state], where
    [Candidate #1] currently has a [NN] percent chance of winning.
    
    If [NN] percent of pledged swaps vote like they pledge, we calculate that
    [Candidate #1] has a [NN] percent chance of winning.

    [I pledge to swap my vote] [Cancel]
9. After pledging the user can agree to sign up for a mailing list. Their email
will not be linked to their vote swap pledge and it will only be used for
updates. The user may click a checkbox that says "Delete my email address after
the election". Emails will not be stored in an encrypted state, except for
disk encryption used on the database server.

# Uncertainty

How can we get a gauge on a user's truthfulness? I suspect the majority of
users will not vote like they pledge. By asking users how likely they think
they are to vote like they pledge, and how likely they think others are, we
can get a feeling for the likelihood of users defecting in this prisoner's
dilemma.

When users are paired we need to tell each user how likely the paired user is
to vote like they pledged. If my paired user rated themselves 5/5 likely to vote
for their pledge, it would increase my own chances of voting like I pledged.
Defection is always an attractive strategy in the prisoner's dilemma, but
*maybe* this will help reduce the incidence.

TODO: Talk to a statistician and a pollster. Try to contact Eliezer to use his
network of smart people to figure this out.

# Calculating chance of winning given pledge swaps

We should display live likelihood of each candidate winning in each state with
and without the swaps, along with the distribution given all users' likelihood
to follow through with their vote pledge.

I'm out of my league here, need a stats person.

# Matching a pledge

Some options:

## Election day pairing

Maybe pledges shouldn't be matched until election day. On that day people
are paired in order of likelihood of voting like they pledge. How to convince
people during sign up flow, then? If a user isn't convinced it's going to work
maybe they'll bail out.

## Preferential state selection pairing

Pledge to vote for C#2 in my state if someone in [other state] votes C#1. Pair
as soon as someone pledges to vote for C#1 and they meet some minimum
likelihood. If a match isn't available state the pledge is recorded and they'll
be paired soon, if one is available then text both parties with the likelihood
of each other voting.

## Immediate greedy pairing

Ignore everything and match up 1-for-1 regardless of state or chances of C#1
winning that state.
