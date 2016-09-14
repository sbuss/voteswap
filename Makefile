PYTHONPATH=PYTHONPATH=$(PWD)/lib

lib: requirements-vendor.txt
	rm -rf $@
	mkdir -p $@
	pip install -t $@ -r requirements-vendor.txt


.PHONY: setup
setup: lib requirements-test.txt requirements-local.txt
	pip install -r requirements-local.txt
	pip install -r requirements-test.txt

.PHONY: setupdb
setupdb: deps
	$(PYTHONPATH) python manage.py migrate
	@#$(PYTHONPATH) python manage.py createsuperuser
	@#$(PYTHONPATH) python manage.py dumpdata
	$(PYTHONPATH) python manage.py loaddata fixtures/*.json

.PHONY: startcontainer
startcontainer:
	./startcontainers.sh

.PHONY: deps
deps: startcontainer

.PHONY: stop
stop:
	-docker stop voteswap-mysql
	-docker rm voteswap-mysql

test: deps setup
	$(PYTHONPATH) python manage.py test
