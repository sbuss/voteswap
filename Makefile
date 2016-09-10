PYTHONPATH=PYTHONPATH=$(PWD)/lib

lib: requirements-vendor.txt
	mkdir -p $@
	pip install -t $@ -r requirements-vendor.txt


.PHONY: setup
setup: lib
	pip install -r requirements-local.txt

.PHONY: setupdb
setupdb: startcontainer
	$(PYTHONPATH) python manage.py migrate
	$(PYTHONPATH) python manage.py createsuperuser
	$(PYTHONPATH) python manage.py dumpdata

.PHONY: startcontainer
startcontainer: stop
	./startcontainers.sh

.PHONY: deps
deps: startcontainer

.PHONY: stop
stop:
	-docker stop mysql-voteswap
	-docker rm mysql-voteswap
