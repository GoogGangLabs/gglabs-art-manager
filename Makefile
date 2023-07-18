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

.PHONY: external-lib
external-lib:
	mkdir -p $(APP)/external_lib lib
	pushd $(GLTF_FORMATTER_PATH) && make build && popd
	cp -r $(GLTF_FORMATTER_PATH)/build/lib/* $(APP)/external_lib/
	cp $(GLTF_FORMATTER_PATH)/dist/*.whl lib/


.PHONY: clean
clean:
	pushd $(GLTF_FORMATTER_PATH) && make clean && popd
	rm -rf lib $(APP)/external_lib build

.PHONY: build
build: external-lib
	mkdir -p build
	zip -vr build/$(APP).zip $(APP) -x "*.DS_Store" -x "*.pyc" -x "*__pycache__*"
	zip -vr build/sample.zip sample

dev: external-lib venv

blender:
	PYTHONPATH=$(PWD) $(BLENDER) --python $(SRC)/__init__.py sample/sample.blend
