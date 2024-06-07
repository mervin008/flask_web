#!/bin/bash

python3 -m venv env
# virtal env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Gunicorn
gunicorn --bind 0.0.0.0:8000 app:app &  
