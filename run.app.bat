@echo off
cd /d "%~dp0"
call venv_py311\Scripts\activate
python LoginMain.py
pause