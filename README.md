# Kikitown Pipeline Mananger

### Description

* Export art resources (glbs) that is compatible and flawless to be used within Kikitown development/service enviroment.
* Automate the tedious aspects within the workflows involved in building 3D models.

### Prerequisites

* Blender (>= 3.4)
* Python (>= 3.10)
* `make`
* vscode
* Export `${BLENDER}` environment variable as actual installed path.
    * e.g. `export BLENDER=/Applications/Blender.app/Contents/MacOS/Blender`

### Development

* Setup venv: `make venv`
* Run linter on python codes: `make lint`
* Format python codes: `make format`
* Run test: `make test`
* Build an addon artifact (zip file): `make build`
* Open a sample blender file with addon: `make blender`

### 
