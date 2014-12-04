@echo off
rmdir /s /q build
% del source\pphelper.rst
% del source\modules.rst
% sphinx-apidoc -f -o source ..\pphelper ..\pphelper\version.py ..\pphelper\tests
make html
