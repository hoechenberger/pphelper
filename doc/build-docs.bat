@echo off
rmdir /s /q build
REM del source\pphelper.rst
REM del source\modules.rst
REM sphinx-apidoc --no-toc -f -o source ..\pphelper ..\pphelper\version.py ..\pphelper\tests
make html
