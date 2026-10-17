PYTHON ?= python3
SKILL ?=
INSTALL_ARGS ?=

.DEFAULT_GOAL := help
.PHONY: help catalog install install-codex install-cursor install-claude check test examples resources setup-hooks secret-check

help:
	@$(PYTHON) scripts/skills.py --help
	@echo "make catalog | install-codex | install-cursor | install-claude | install | examples | resources | check"
	@echo "Contributor security: make setup-hooks | secret-check"
	@echo 'Select one skill: make install-codex SKILL=context-templates'
	@echo 'Preview: make install INSTALL_ARGS=--dry-run'

catalog:
	$(PYTHON) scripts/skills.py list

install:
	$(PYTHON) scripts/skills.py install --agent all $(if $(SKILL),--skill "$(SKILL)") $(INSTALL_ARGS)

install-codex:
	$(PYTHON) scripts/skills.py install --agent codex $(if $(SKILL),--skill "$(SKILL)") $(INSTALL_ARGS)

install-cursor:
	$(PYTHON) scripts/skills.py install --agent cursor $(if $(SKILL),--skill "$(SKILL)") $(INSTALL_ARGS)

install-claude:
	$(PYTHON) scripts/skills.py install --agent claude $(if $(SKILL),--skill "$(SKILL)") $(INSTALL_ARGS)

examples:
	$(PYTHON) scripts/dynamic_umls.py

resources:
	$(PYTHON) scripts/ct_lifecycle.py

setup-hooks:
	pre-commit install --allow-missing-config

secret-check:
	$(PYTHON) scripts/secret_scan.py --history
	gitleaks git --redact --log-opts="--all" .

check:
	$(PYTHON) scripts/check_code_size.py
	$(PYTHON) scripts/dynamic_umls.py --check
	$(PYTHON) scripts/ct_lifecycle.py --check
	$(PYTHON) scripts/skills.py check
	$(PYTHON) scripts/secret_scan.py
	$(MAKE) test

test:
	$(PYTHON) -m unittest discover -s tests -v
