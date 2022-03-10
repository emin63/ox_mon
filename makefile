
SHELL = /bin/bash

.PHONY: help test test_fails trouble clean help_venv check_env reqs

# Define PROJECT to be the top-level name of your project.
PROJECT=ox_mon

# Define the minimum coverage precentage allowed
COV_MIN=78

# Set python executable
PYTHON=python3

.EXPORT_ALL_VARIABLES:


################################################################
#                                                              #
#  IGNORE gets added to for stuff tester should ignore. #
#  Note that we need := for assignment to keep appending       #

IGNORE = 

# Ignore setup.py
IGNORE := ${IGNORE} setup.py

# Ignore venv
IGNORE := ${IGNORE} venv_${PROJECT} venv

FLAKE8_IGNORE = $(foreach thing,$(IGNORE),--exclude ${thing})
PYTEST_IGNORE = $(foreach thing,$(IGNORE),--ignore ${thing})
PYLINT_IGNORE = $(foreach thing,$(IGNORE),--ignore ${thing})


# End PYTEST_IGNORE section                                    #
#                                                              #
################################################################

PYTEST_TARGET = ${PROJECT} tests

# Set the cov target to ${PROJECT} so we ignore venv
PYTEST_COV = --cov=${PROJECT} --cov-report term-missing \
  --cov-fail-under ${COV_MIN}


PYTEST_FLAGS = -vvv --doctest-modules --doctest-glob='*.md'
PYTEST_EXTRA_FLAGS = 

help:
	@echo "This is a makefile for basic operations."
	@echo ""
	@echo "reqs:           Update requirements (make sure to activate venv)"
	@echo "test:           Run regression tests via pytest."
	@echo "test_fails:     Run tests that failed previous run."
	@echo "test_no_cov:    Run tests without coverage report."
	@echo "help_venv:      Help on using virtual environments"

reqs:
	@if which pip | grep venv_ ; then echo "updating" ; else \
            echo "" && echo "suspicious pip does not look like venv; exit" && \
            echo "" && echo "Have you sourced your venv?" && \
            echo "Try 'make help_venv'" && echo "" && exit 1; fi
	pip install -r requirements.txt

clean:
	rm -rf .pytype
	find . -name \*_flymake.py -print -exec rm {} \;
	find . -name '*~' -print -exec rm {} \;
	find ${PROJECT} -name '*.pyc' -print -exec rm {} \;
	find . -name '*.pyi' -print -exec rm {} \;
	find . -name archived_logs -print -exec rm -fr {} \;
	find . -name latest_logs -print -exec rm -fr {} \;
	@echo "done cleaning"

# Note that we set pipefail on the command since `tee` always returns status 0
# so we need pipefail if we want this command to fail on test failure.
test:
	set -o pipefail && \
          py.test ${PYTEST_COV} ${PYTEST_FLAGS} ${PYTEST_IGNORE} \
            ${PYTEST_EXTRA_FLAGS} ${PYTEST_TARGET} 2>&1 | tee ./test_log.txt

lint:
	flake8 ${PYTEST_TARGET} ${FLAKE8_IGNORE}
	pylint --rcfile=.pylintrc --jobs=4 --reports=n \
           ${PYTEST_TARGET} ${PYLINT_IGNORE}

pytype:
	pytype ${PYTEST_TARGET}

check:
	${MAKE} lint
	${MAKE} pytype
	${MAKE} test

test_no_cov:
	${MAKE} test PYTEST_COV=

test_fails:
	${MAKE} PYTEST_COV= \
            PYTEST_EXTRA_FLAGS="${PYTEST_EXTRA_FLAGS} --last-failed" test

help_venv:
	@echo "You need to setup a python virtual env to install packages to."
	@echo "Do '${PYTHON} -m venv venv_${PROJECT}' to activate virtual env"
	@echo "After that, do 'source venv_${PROJECT}/bin/activate'"
	@echo "to activate your virtual environment."

pypi: README.rst check
	 ${PYTHON} setup.py sdist upload -r pypi

README.rst: README.org
	pandoc --from=org --to=rst --output=README.rst README.org
