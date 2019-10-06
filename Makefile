.PHONY: all
all:

.PHONY: mypy
mypy:
	MYPYPATH=stubs mypy --config-file mypy.conf src/davclient src/dav.py
