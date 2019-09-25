#!/bin/bash

echo "Starting Server"

source env/bin/activate
cd FusionIIIT/
python3 manage.py runserver

