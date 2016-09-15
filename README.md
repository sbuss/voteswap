# voteswap.us

[Vote swapping](https://en.wikipedia.org/wiki/Vote_pairing) lets you vote your
conscience *and* for the lesser evil. It is the only way to vote for a
third-party candidate that you know will lose without giving up your state
to the candidate you like the least.

# How does it work?

When you sign up for voteswap you will be asked for your preferred candidate.
If that candidate is one of the top two candidates (Donald J. Trump or Hillary
Clinton) then you're done for now. If not, you will be asked for your 
second-choice candidate and your state.

If you live in a swing state and want to vote for a third-party candidate, you
will be paired up with a friend in a safe state for your second-choice
candidate and you and your friend will swap votes. You will vote for your
second choice, and your friend will vote for your first choice. The popular vote
for each candidate is unchanged, but your state goes to your second choice.

This lets voters signal their frustration with the two-party system while not
letting the least favored candidate win due to a third party stealing votes
from one of the big two.

Here are two concrete examples to help explain:

Alice lives in California, a safe Clinton state, and wants to vote for Clinton.
Bob lives in Florida, an important swing state, and wants to vote for Johnson,
but would prefer Clinton win instead of Trump. Alice and Bob decide to use
voteswap.us to swap their votes. On election day Bob votes Clinton in Florida,
ensuring her win in the state, and Alice votes for Johnson in California, which
doesn't matter to Clinton because there's no way she'd lose there. Clinton's
win in Florida carries her to victory and Alice and Bob are both happy.

Charlie lives in Wyoming, a safe Trump state, and wants to vote for Trump.
David lives in North Carolina and wants to vote for Johnson, but would prefer
Trump win instead of Clinton. They pair up on voteswap.us and pledge to swap.
On election day Charlie votes Johnson in Wyoming and David votes Trump in
North Carolina, ensuring that North Carolina doesn't fall into the hands of
Clinton. Trump's win in North Carolina carries him to victory and both Charlie
and David are happy.

In both cases, the popular vote doesn't change -- there's still one vote for
each candidate, but the swing states are made safe for the second choice
candidate. This ensures that the "lesser of two evils" wins the election, and
shows a very high proportion of the US would prefer a third party.

## After the election

After the election, while the shockingly high third-party turnout is still on
everyone's minds, we can start a dialogue on changing our election process to
use ranked choice voting, aka [instant runoff elections](https://en.wikipedia.org/wiki/Instant-runoff_voting).
This system of voting lets you write down your candidates in order, allowing
votes for third parties to not take away from votes for other parties.

# Contributing

We'd love to get your help on this project. All pull requests and issues will
be considered in a timely manner.

# Development

```sh
virtualenv venv
. venv/bin/activate
export PYTHONPATH=$(pwd)/lib:$PYTHONPATH
make setup
# Install docker via, eg:
# OSX: brew install docker
# or Linux: https://docs.docker.com/engine/installation/linux/ubuntulinux/ (ugh)
# If this is your first time, run
make setupdb
# Otherwise, just run
make deps
```
