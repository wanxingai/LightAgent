SHELL := /bin/bash
POETRY := uv tool run --from poetry==2.4.1 poetry

help: ## This help
	@echo -e "$$(grep -hE '^\S+:.*##' $(MAKEFILE_LIST) | sed -e 's/:.*##\s*/:/' -e 's/^\(.\+\):\(.*\)/\\x1b[36m\1\\x1b[m:\2/' | column -c2 -t -s :)"

check-tools: ## Check tools are installed
	@echo "Checking uv is installed"
	@command -v uv

setup: check-tools  ## Set up local environment
	$(POETRY) install --with dev

update: check-tools ## Update local dependencies
	$(POETRY) lock
	$(POETRY) install --with dev

build: check-tools ## Build Wheel
	$(POETRY) build --format wheel
