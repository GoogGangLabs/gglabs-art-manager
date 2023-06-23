include .Makefile.venv

APP=kikitown_pipeline_manager
BIN=./.venv/bin
SRC=./$(APP)

PY=python3.10

UNAME := $(shell uname -s)
ifeq ($(UNAME), Linux)
	OS:="ubuntu"
else ifeq ($(UNAME), Darwin)
	OS:="mac"
else
	OS := ""
endif

EXTERNAL_PKGS=et_xmlfile openpyxl
DST_EXTERNAL_DIR=$(SRC)/external_lib
SRC_EXTERNAL_PKGS := $(addprefix $(VENVDIR)/lib/python*/site-packages/,$(EXTERNAL_PKGS))

.PHONY: $(DST_EXTERNAL_DIR)
$(DST_EXTERNAL_DIR): $(SRC_EXTERNAL_PKGS)
	mkdir -p $(DST_EXTERNAL_DIR)
	cp -r $^ $@

echo-blender:
	$(BLENDER) --version

.PHONY: lint
lint:
	$(BIN)/pylint $(SRC)

.PHONY: format
format:
	$(BIN)/black $(SRC)

.PHONY: test
test:
	$(BIN)/pytest -vvv $(SRC)/test

.PHONY: external-lib
external-lib: $(DST_EXTERNAL_DIR)

.PHONY: build
build: external-lib
	mkdir -p build
	zip -vr build/$(APP)_$(OS).zip $(APP) -x "*.DS_Store" -x "*.pyc" -x "*__pycache__*"
	zip -vr build/sample.zip sample

blender: venv
	PYTHONPATH=$(PWD) $(BLENDER) --python $(SRC)/__init__.py sample.blend
