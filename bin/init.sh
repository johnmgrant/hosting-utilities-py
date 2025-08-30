#!/bin/bash

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# If the environment is not already sourced, source it.
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

python -m pip install --no-warn-script-location -r requirements.txt