#!/bin/bash

module load python/3.6.0

python3 -m venv --copies .env
source .env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
