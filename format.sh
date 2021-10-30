#!/bin/sh

set -e

echo Running autoflake
autoflake --expand-star-imports --remove-all-unused-imports --ignore-init-module-imports --remove-unused-variables --in-place -r .
echo Running isort
isort --profile black --skip .env --skip .dev.env .
echo Running black
black . --exclude .dev.env --exclude .env
echo Running mypy
mypy --ignore-missing-imports  --install-types --non-interactive --disallow-untyped-defs --disallow-incomplete-defs --pretty main.py train.py
