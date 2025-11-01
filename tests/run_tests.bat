@echo off
rem NeuroHub Test Runner for Windows
rem This script runs the complete test suite for NeuroHub

echo ==============================
echo NeuroHub Test Suite Runner
echo ==============================

set PYTHON_EXE=%~dp0venv\Scripts\python.exe
set PYTEST_EXE=%~dp0venv\Scripts\pytest.exe

if not exist "%PYTHON_EXE%" (
    echo Error: Python virtual environment not found
    echo Please run: python -m venv venv
    exit /b 1
)

echo Python executable: %PYTHON_EXE%
echo.

if "%1"=="--python" goto :python_tests
if "%1"=="--coverage" goto :coverage_tests
if "%1"=="--all" goto :all_tests
if "%1"=="--shell" goto :shell_tests

:default_tests
echo Running default Python tests...
"%PYTEST_EXE%" tests/ -v
goto :end

:python_tests
echo Running Python unit tests...
"%PYTEST_EXE%" tests/ -v
if "%2"=="--coverage" goto :coverage_tests
goto :end

:coverage_tests
echo Running tests with coverage...
"%PYTEST_EXE%" tests/ --cov=agents --cov=services --cov-report=html --cov-report=term -v
echo.
echo Coverage report generated in htmlcov/index.html
goto :end

:shell_tests
echo Running shell tool tests...
if exist "tests\tools\test_git_commit_ai.sh" (
    bash tests\tools\test_git_commit_ai.sh
) else (
    echo Shell tests not found or bash not available
)
goto :end

:all_tests
echo Running complete test suite...
echo.
echo 1. Python unit tests with coverage...
"%PYTEST_EXE%" tests/ --cov=agents --cov=services --cov-report=html --cov-report=term -v
echo.
echo 2. Shell tool tests...
if exist "tests\tools\test_git_commit_ai.sh" (
    bash tests\tools\test_git_commit_ai.sh
) else (
    echo Shell tests not found or bash not available
)
echo.
echo All tests completed!
goto :end

:end
echo.
echo ==============================
echo Test execution finished
echo ==============================
