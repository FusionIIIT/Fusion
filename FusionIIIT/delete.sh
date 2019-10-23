#!/bin/bash

find . | grep -E "(__pycache__|\.pyc|\.pyo$|.\__init__.py)" | xargs rm -rf
find . | grep -E "(migrations)" | xargs rm -rf
