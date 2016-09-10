lib: requirements-vendor.txt
	mkdir -p $@
	pip install -t $@ -r requirements-vendor.txt


setup: lib
	pip install -r requirements-local.txt
