include .Makefile.venv
include .env

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

EXTERNAL_PKGS=blender_validator gltf_formatter dataclasses_json deprecated extensions marshmallow mypy_extensions.py packaging pygltflib typing_extensions.py typing_inspect.py wrapt

DST_EXTERNAL_DIR=$(SRC)/external_lib
SRC_EXTERNAL_PKGS := $(addprefix $(VENVDIR)/lib/python*/site-packages/,$(EXTERNAL_PKGS))

SAMPLE?=sample/sample.blend

.PHONY: $(DST_EXTERNAL_DIR)
$(DST_EXTERNAL_DIR): $(SRC_EXTERNAL_PKGS)
	mkdir -p $(DST_EXTERNAL_DIR)
	cp -r $^ $@


echo-blender:
	$(BLENDER) --version
	$(BLENDER) -b --python-expr "import sys;print(f'\n{sys.executable}\n')"


.PHONY: lint
lint:
	$(BIN)/pylint $(SRC)

.PHONY: format
format:
	$(BIN)/black $(SRC)

.PHONY: test
test:
	$(BIN)/pytest -vvv $(SRC)/test

.PHONY: copy-lib
copy-lib:
	mkdir -p lib
	pushd $(GLTF_FORMATTER_PATH) && make build && popd
	cp $(GLTF_FORMATTER_PATH)/dist/*.whl lib/

.PHONY: install-lib
install-lib: copy-lib
	$(BIN)/python -mpip install --force-reinstall lib/*.whl

.PHONY: dev
dev: copy-lib venv install-lib

.PHONY: external-lib
external-lib: $(DST_EXTERNAL_DIR)

.PHONY: build
build: external-lib
	mkdir -p build
	zip -vr build/$(APP).zip $(APP) -x "*.DS_Store" -x "*.pyc" -x "*__pycache__*"
	zip -vr build/sample.zip sample

.PHONY: clean
clean:
	pushd $(GLTF_FORMATTER_PATH) && make clean && popd
	rm -rf lib $(APP)/external_lib build

blender: external-lib
	PYTHONPATH=$(PWD) $(BLENDER) --python $(SRC)/__init__.py $(SAMPLE)
