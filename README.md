# VoteSwap.us

Vote Swapping is the only way to make third-party candidates viable given the
current US election process.


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
