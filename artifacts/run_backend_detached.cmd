@echo off
cd /d C:\Users\bhara\Fusion\FusionIIIT
"C:\Users\bhara\Fusion\venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000 --noreload 1> "C:\Users\bhara\Fusion\artifacts\backend-detached-stdout.log" 2> "C:\Users\bhara\Fusion\artifacts\backend-detached-stderr.log"
