PYTHON ?= python3
SKILL ?=
INSTALL_ARGS ?=

.DEFAULT_GOAL := help
.PHONY: help catalog install install-codex install-cursor install-claude check test build examples resources

help:
	@$(PYTHON) scripts/skills.py --help
	@echo "make catalog | install-codex | install-cursor | install-claude | install | examples | resources | check | build"
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

check:
	$(PYTHON) scripts/dynamic_umls.py --check
	$(PYTHON) scripts/ct_lifecycle.py --check
	$(PYTHON) scripts/skills.py check
	$(MAKE) test

test:
	$(PYTHON) -m unittest discover -s tests -v

build:
	$(PYTHON) scripts/dynamic_umls.py --check
	$(PYTHON) scripts/ct_lifecycle.py --check
	$(PYTHON) scripts/skills.py build
