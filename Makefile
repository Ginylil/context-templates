#!make
.ONESHELL:
.EXPORT_ALL_VARIABLES:
.PHONY: all $(MAKECMDGOALS)


UNAME := $(shell uname)
BASH_PATH:=$(shell which bash)
ROOT_DIR:=${CURDIR}

# Global .env
ifneq ("$(wildcard ${ROOT_DIR}/.env)","")
include ${ROOT_DIR}/.env
endif

VENV_DIR_PATH:=${ROOT_DIR}/.VENV

ifndef REQUIREMENTS_FILE_PATH
REQUIREMENTS_FILE_PATH:=${ROOT_DIR}/requirements.txt
endif

# --- OS Settings --- START ------------------------------------------------------------
# Windows
ifneq (,$(findstring NT, $(UNAME)))
_OS:=windows
VENV_BIN_ACTIVATE:=${VENV_DIR_PATH}/Scripts/activate.bat
endif
# macOS
ifneq (,$(findstring Darwin, $(UNAME)))
_OS:=macos
VENV_BIN_ACTIVATE:=${VENV_DIR_PATH}/bin/activate
endif

ifneq (,$(findstring Linux, $(UNAME)))
_OS:=linux
VENV_BIN_ACTIVATE:=${VENV_DIR_PATH}/bin/activate
endif
# --- OS Settings --- END --------------------------------------------------------------

SHELL:=${BASH_PATH}

# Automatically activate virtual environment if it exists
ifneq (,$(wildcard ${VENV_BIN_ACTIVATE}))
ifeq (${_OS},macos)
SHELL:=source ${VENV_BIN_ACTIVATE} && ${SHELL}
endif
ifeq (${_OS},windows)
SHELL:=${VENV_BIN_ACTIVATE} && ${SHELL}
endif
ifeq (${_OS},linux)
SHELL:=source ${VENV_BIN_ACTIVATE} && ${SHELL}
endif
endif

ifeq (${CI},true)
SHELL:=${BASH_PATH}
endif

# Removes blank rows - fgrep -v fgrep
# Replace ":" with "" (nothing)
# Print a beautiful table with column
help: ## Print this menu
	@echo
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's~:.* #~~' | column -t -s'#'
	@echo
usage: help


# To validate env vars, add "validate-MY_ENV_VAR"
# as a prerequisite to the relevant target/step
validate-%:
	@if [[ -z '${${*}}' ]]; then \
		echo 'ERROR: Environment variable $* not set' && \
		exit 1 ; \
	fi

print-vars: ## Print env vars
	@echo "VENV_BIN_ACTIVATE=${VENV_BIN_ACTIVATE}"
	@echo "REQUIREMENTS_FILE_PATH=${REQUIREMENTS_FILE_PATH}"
	@echo "VENV_DIR_PATH=${VENV_DIR_PATH}"
	@echo "CI=${CI}"


prepare-dotenv:
	@if [ -f .env ] ; then : ; else ${ROOT_DIR}/scripts/dotenv.sh ${ROOT_DIR}/env.template ${ROOT_DIR}/.env ; fi


# --- VENV --- START ------------------------------------------------------------
## 
##VENV
##----
prepare: ## Create a Python virtual environment with venv
	python -m venv ${VENV_DIR_PATH} && \
	python -m pip install -U pip wheel setuptools build twine ruff && \
	ls ${VENV_DIR_PATH}

install: ## Install Python packages
## Provide PACKAGE_NAME=<package_name> to install a specific package
## Example: make venv-install PACKAGE_NAME=requests
	@cd ${ROOT_DIR} && \
	if [[ -f "${REQUIREMENTS_FILE_PATH}" ]]; then \
		echo "Installing packages from ${REQUIREMENTS_FILE_PATH}" && \
		ls ${REQUIREMENTS_FILE_PATH} && \
		pip install -r "${REQUIREMENTS_FILE_PATH}" ${PACKAGE_NAME} ; \
	elif [[ -n "${PACKAGE_NAME}" ]]; then \
		echo "Installing package ${PACKAGE_NAME}" ; \
		pip install -U ${PACKAGE_NAME} ; \
	else \
		echo "ERROR: No requirements.txt file found and no package name provided" ; \
		exit 1 ; \
	fi

requirements-update: ## Update requirements.txt with current packages
	cd ${ROOT_DIR} && \
	pip freeze | grep -v '\-e' > ${REQUIREMENTS_FILE_PATH} && \
	cat ${REQUIREMENTS_FILE_PATH}

venv-freeze: ## List installed packages
	cd ${ROOT_DIR} && \
	pip freeze


format: ## Format code
	ruff format .

lint: ## Lint code
	ruff check --fix .

push-templates:
	cd ${ROOT_DIR} && \
		python scripts/push_templates.py
# --- VENV --- END --------------------------------------------------------------
