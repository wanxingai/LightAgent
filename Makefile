SHELL := /bin/bash

help: ## This help
	@echo -e "$$(grep -hE '^\S+:.*##' $(MAKEFILE_LIST) | sed -e 's/:.*##\s*/:/' -e 's/^\(.\+\):\(.*\)/\\x1b[36m\1\\x1b[m:\2/' | column -c2 -t -s :)"

check-tools: ## Check tools are installed
	@echo "Checking uv is installed"
	@command -v uv

setup: check-tools  ## Set up local environment
	uv tool install poetry
	uv tool run poetry install 

update: check-tools ## Update local dependencies
	uv tool update poetry
	uv tool run poetry lock
	uv tool run poetry install

build: check-tools ## Build Wheel
	uv tool run poetry build --format wheel

