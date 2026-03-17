#!/bin/bash
# Update poetry.lock file to match pyproject.toml

echo "Updating poetry.lock..."
pip install --quiet poetry
poetry lock --no-update
echo "✓ poetry.lock updated successfully"
