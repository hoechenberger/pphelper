#!/usr/bin/env sh

sphinx-apidoc -o source ../pphelper ../pphelper/version.py ../pphelper/tests
make html