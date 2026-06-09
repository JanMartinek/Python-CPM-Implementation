@echo off
REM CPM Python Implementation - Windows Build Script
REM Usage: make.bat [target]

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="install" goto install
if "%1"=="install-dev" goto install-dev
if "%1"=="test" goto test
if "%1"=="test-verbose" goto test-verbose
if "%1"=="test-coverage" goto test-coverage
if "%1"=="test-specific" goto test-specific
if "%1"=="examples" goto examples
if "%1"=="clean" goto clean
if "%1"=="all" goto all
goto help

:help
echo CPM Python Implementation - Build Script
echo.
echo Available targets:
echo   install        - Install core dependencies
echo   install-dev    - Install all dependencies (including dev/optional)
echo   test           - Run all tests (quiet mode)
echo   test-verbose   - Run all tests with verbose output
echo   test-coverage  - Run tests with coverage report
echo   test-specific  - Run template tests only
echo   examples       - Run all example scripts
echo   clean          - Remove build artifacts and cache files
echo   all            - Install deps and run tests
goto end

:install
echo Installing core dependencies...
pip install -r requirements.txt
goto end

:install-dev
echo Installing all dependencies...
pip install -r requirements.txt
pip install -e .
goto end

:test
echo Running tests (quiet mode)...
python -m pytest tests/ -q
goto end

:test-verbose
echo Running tests (verbose mode)...
python -m pytest tests/ -v
goto end

:test-coverage
echo Running tests with coverage...
python -m pytest tests/ --cov=src --cov-report=html --cov-report=term
goto end

:test-specific
echo Running template tests...
python -m pytest tests/template/test_template.py -v
goto end

:examples
set PYTHONPATH=.;%PYTHONPATH%
echo Running basic examples...
python examples/basic_examples.py
echo.
echo Running advanced examples...
python examples/advanced_examples.py
echo.
echo Running template examples...
python examples/template_examples.py
echo.
echo Running advanced template examples...
python examples/template_advanced_examples.py
echo.
echo Running CpmDocument examples...
python examples/cpmdocument_examples.py
echo.
echo Running BBMRI biobank use case...
python examples/usecases/usecase_bbmri_biobank.py
echo.
echo Running MOU XML use case...
python examples/usecases/usecase_mou_xml.py
echo.
echo Running EMBRC JSON-LD use case...
python examples/usecases/usecase_embrc_jsonld.py
goto end

:clean
echo Cleaning build artifacts...
if exist __pycache__ rmdir /s /q __pycache__
if exist .pytest_cache rmdir /s /q .pytest_cache
if exist .coverage del /q .coverage
if exist htmlcov rmdir /s /q htmlcov
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
for /d /r %%d in (*.egg-info) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul
echo Clean complete!
goto end

:all
call :install
call :test
echo Setup complete and all tests passed!
goto end

:end
