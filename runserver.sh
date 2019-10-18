#!/bin/bash

echo "--------------------------------------------Activating Environment--------------------------------------------"

source env/bin/activate
cd FusionIIIT/

echo "-------------------------------------------Starting Server-----------------------------------------------------"
python3 manage.py runserver

