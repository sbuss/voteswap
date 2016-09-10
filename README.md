# VoteSwap.us

Vote Swapping is the only way to make third-party candidates viable given the
current US election process.

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
make deps  # this runs mysql
```
