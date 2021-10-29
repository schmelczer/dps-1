#!/bin/bash

module load python/3.6.0
module load prun

source .env/bin/activate

python3 setup_nodes.py
