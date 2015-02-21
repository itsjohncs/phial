#!/usr/bin/env bash

RED="\033[0;31m"
GREEN="\033[0;32m"
RESET="\033[0m"

hash flake8 2>/dev/null || { echo >&2 "flake8 is not installed (pip install flake8)"; exit 1; }

flake8
lint_status=$?

if [ $lint_status -ne 0 ]; then
	echo >&2 -e ${RED}One or more lint checks failed.$RESET
else
	echo -e ${GREEN}All lint checks passed.$RESET
fi
exit $lint_status
