# ugh, appengine why can't I just pip install you?!
PYTHONPATH=PYTHONPATH=$(PWD)/lib:$(shell echo $$PYTHONPATH)

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

.PHONY: genfixtures
genfixtures: deps
	$(PYTHONPATH) python manage.py migrate
	$(PYTHONPATH) python manage.py createsuperuser
	@echo "Run the following:"
	@echo "from fixtures import generate_random_network"
	@echo "generate_random_network.create_profiles(100)"
	@echo "generate_random_network.assign_friends()"
	@echo "from polling.load_data import load_fixture"
	@echo "load_fixture('polling/data/2016-09-11.tsv')"
	$(PYTHONPATH) python manage.py shell
	$(PYTHONPATH) python manage.py dumpdata -o fixtures/users.json
	sed -i 's/}},/}},\n/g' fixtures/users.json

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

.PHONY: runserver
runserver: deps
	$(PYTHONPATH) python manage.py runserver
