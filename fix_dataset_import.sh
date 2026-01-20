#!/bin/bash

set -e

echo "============================================================"
echo "APLOSE Dataset Import Fix Script"
echo "============================================================"
echo ""

echo "This script will:"
echo "  1. Regenerate the netcdf_example dataset with correct structure"
echo "  2. Clear Python cache files"
echo "  3. Rebuild Docker containers completely"
echo "  4. Test the dataset import"
echo ""
read -p "Press Enter to continue..."

# Step 1: Remove old dataset
echo "1. Removing old dataset..."
if [ -d "volumes/datawork/dataset/netcdf_example" ]; then
    rm -rf volumes/datawork/dataset/netcdf_example
    echo "✓ Removed old dataset"
else
    echo "  No old dataset found"
fi
echo ""

# Step 2: Regenerate dataset using the generator script
echo "2. Regenerating dataset with correct structure..."
python3 examples/generate_netcdf_dataset.py --output volumes/datawork/dataset --name netcdf_example
echo "✓ Dataset regenerated"
echo ""

# Step 3: Verify JSON files have 'data' field
echo "3. Verifying JSON structure..."
echo "  Checking dataset.json..."
if grep -q '"datasets"' volumes/datawork/dataset/netcdf_example/dataset.json; then
    echo "  ✓ dataset.json looks good"
else
    echo "  ✗ dataset.json is malformed"
    exit 1
fi

echo "  Checking original.json..."
if grep -q '"data"' volumes/datawork/dataset/netcdf_example/data/audio/original/original.json; then
    echo "  ✓ original.json has 'data' field"
else
    echo "  ✗ original.json is missing 'data' field"
    exit 1
fi

echo "  Checking netcdf_analysis.json..."
if grep -q '"data"' volumes/datawork/dataset/netcdf_example/processed/netcdf_analysis/netcdf_analysis.json; then
    echo "  ✓ netcdf_analysis.json has 'data' field"
else
    echo "  ✗ netcdf_analysis.json is missing 'data' field"
    exit 1
fi
echo "✓ All JSON files verified"
echo ""

# Step 4: Clear Python cache in backend
echo "4. Clearing Python cache..."
find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find backend -type f -name "*.pyc" -delete 2>/dev/null || true
echo "✓ Python cache cleared"
echo ""

# Step 5: Stop containers
echo "5. Stopping Docker containers..."
docker compose --env-file test.env down 2>/dev/null || true
echo "✓ Containers stopped"
echo ""

# Step 6: Remove Docker volumes (optional but recommended)
echo "6. Removing Docker volumes to clear any cached data..."
read -p "Remove Docker volumes? This will clear the database. (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker compose --env-file test.env down -v
    echo "✓ Volumes removed"
else
    echo "  Skipped volume removal"
fi
echo ""

# Step 7: Rebuild containers with --no-cache
echo "7. Rebuilding Docker containers (this may take a while)..."
docker compose --env-file test.env build --no-cache osmose_back
echo "✓ Backend rebuilt"
echo ""

# Step 8: Start containers
echo "8. Starting Docker containers..."
docker compose --env-file test.env up -d
echo "✓ Containers started"
echo ""

# Step 9: Wait for services
echo "9. Waiting for services to be ready..."
sleep 15
echo "✓ Services should be ready"
echo ""

# Step 10: Check backend logs for errors
echo "10. Checking backend logs for errors..."
docker compose --env-file test.env logs osmose_back | tail -30
echo ""

echo "============================================================"
echo "Fix Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Access APLOSE at: http://localhost:8080"
echo "  2. Login as admin"
echo "  3. Try importing the 'netcdf_example' dataset"
echo ""
echo "If the import still fails:"
echo "  1. Check logs: docker compose --env-file test.env logs osmose_back"
echo "  2. Run test script: docker compose --env-file test.env exec osmose_back python /opt/test_osekit_loading.py"
echo ""
echo "============================================================"
