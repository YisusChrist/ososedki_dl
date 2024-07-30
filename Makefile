# Adapted from https://github.com/Textualize/frogmouth/blob/main/Makefile
##############################################################################
# Path of every file type (. by default if you want it in the current directory)
SRC_DIR     := src
TEST_DIR    := tests
DOC_DIR     := docs

# Common commands
RUN         := poetry run
PYTHON      := $(RUN) python
LINT        := $(RUN) pylint
MYPY        := $(RUN) mypy
BLACK       := $(RUN) black
ISORT       := $(RUN) isort
BANDIT      := $(RUN) bandit
MONKEY      := $(RUN) monkeytype
TEST        := $(RUN) pytest
PYRE        := $(RUN) pyre

# Documentation settings
DOCSRC      := $(DOC_DIR)/source
BUILDDIR    := $(DOC_DIR)/build/html
SPHINXOPTS  := # Add your Sphinx options here

# Package Settings
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))

# Calculate the initial package name from the directory name
initial_package := $(subst -,_,$(notdir $(patsubst %/,%,$(dir $(mkfile_path)))))

# Detect if src folder exists
src_folder_exists := $(wildcard $(SRC_DIR))

ifeq ($(src_folder_exists),)
    # If src folder doesn't exist, use the initial package name
    PACKAGE := $(initial_package)
else
    # If src folder exists, use the initial package name with src/ prefix
    PACKAGE := $(addprefix $(SRC_DIR)/,$(initial_package))
endif

MODULE := $(subst /,.,$(PACKAGE))

##############################################################################
# Methods of running the application.
.PHONY: run
run:				# Run the application
	$(RUN) $(notdir $(patsubst %/,%,$(dir $(mkfile_path))))

.PHONY: debug
debug:				# Run the application in debug mode
	TEXTUAL=devtools make run

##############################################################################
# Setup/update packages the system requires.
.PHONY: setup
setup:				# Set up the development environment
	poetry install
	$(RUN) pre-commit install

.PHONY: update
update:				# Update the development environment
	poetry update

##############################################################################
# Package building and distribution.
.PHONY: build
build:				# Build the package for distribution
	poetry build

.PHONY: clean
clean:				# Clean up the package builds
	rm -rf dist

##############################################################################
# Package publishing.
.PHONY: publish
publish:			# Publish the package to PyPI
	poetry publish --build

.PHONY: publish-test
publish-test:		# Publish the package to TestPyPI
	poetry publish --build -r testpypi

##############################################################################
# Reformatting tools.
.PHONY: black
black:				# Run black over the code
	$(BLACK) $(PACKAGE)

.PHONY: isort
isort:				# Run isort over the code
	$(ISORT) $(PACKAGE)

.PHONY: reformat
reformat: isort black		# Run all the formatting tools over the code

##############################################################################
# Documentation.
doc:                # Build the documentation
	sphinx-quickstart "$(DOC_DIR)"

apidoc:             # Build the API documentation
	sphinx-apidoc -o "$(DOCSRC)" .

html:               # Build the HTML documentation
	sphinx-build "$(DOCSRC)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

livehtml:           # Run a live-updating HTML server for the documentation
	sphinx-autobuild "$(DOCSRC)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

##############################################################################
# Checking/testing/linting/etc.
.PHONY: lint
lint:				# Run Pylint over the library
	$(LINT) $(PACKAGE)

.PHONY: typecheck
typecheck:			# Perform static type checks with mypy
	$(MYPY) --scripts-are-modules $(PACKAGE)

.PHONY: stricttypecheck
stricttypecheck:	# Perform strict static type checks with mypy
	$(MYPY) --scripts-are-modules --strict $(PACKAGE)

.PHONY: bandit
bandit:				# Run bandit over the code
	$(BANDIT) -r $(PACKAGE)

.PHONY: monkey
monkey:				# Run monkeytype over the code
	$(MONKEY) apply $(PACKAGE)

.PHONY: test
test:				# Run the unit tests
	$(TEST) $(TEST_DIR)

.PHONY: checkall
checkall: lint stricttypecheck bandit # Check all the things

##############################################################################
# Utility.
.PHONY: repl
repl:				# Start a Python REPL
	$(PYTHON)

.PHONY: shell
shell:				# Create a shell within the virtual environment
	poetry shell

.PHONY: help
help:				# Display this help
	@grep -Eh "^[a-z]+:.+# " $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.+# "}; {printf "%-20s %s\n", $$1, $$2}'

##############################################################################
# Housekeeping tasks.
.PHONY: housekeeping
housekeeping:		# Perform some git housekeeping
	git fsck
	git gc --aggressive
	git remote update --prune
