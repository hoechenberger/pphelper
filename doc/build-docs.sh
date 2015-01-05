#!/usr/bin/env sh

rm -rf build source/pphelper.rst source/modules.rst
# sphinx-apidoc -o source ../pphelper ../pphelper/version.py ../pphelper/tests
make html
