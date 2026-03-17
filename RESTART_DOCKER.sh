#!/bin/bash
# Restart Docker containers to clear cache and load updated dataset files

echo "Restarting Docker containers..."
docker compose --env-file test.env restart

echo ""
echo "Waiting for services to be ready..."
sleep 5

echo ""
echo "Docker containers restarted!"
echo "Now refresh your browser at http://localhost:8080"
