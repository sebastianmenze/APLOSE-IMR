#!/usr/bin/env python3
"""
Test script to diagnose OSEkit JSON loading issues
"""
import sys
from pathlib import Path

try:
    from osekit.public_api.dataset import Dataset as OSEkitDataset
    from osekit.core_api.audio_dataset import AudioDataset
    print(f"✓ Successfully imported OSEkit")
    print(f"  OSEkit Dataset location: {OSEkitDataset.__module__}")
    print(f"  AudioDataset location: {AudioDataset.__module__}")
except ImportError as e:
    print(f"✗ Failed to import OSEkit: {e}")
    sys.exit(1)

# Test loading the dataset
dataset_path = Path("volumes/datawork/dataset/netcdf_example/dataset.json")

if not dataset_path.exists():
    print(f"✗ Dataset file not found: {dataset_path}")
    sys.exit(1)

print(f"\n✓ Dataset file exists: {dataset_path}")

# Try to load the dataset
try:
    print(f"\nAttempting to load dataset with OSEkitDataset.from_json()...")
    d = OSEkitDataset.from_json(dataset_path)
    print(f"✓ Successfully loaded dataset")
    print(f"  Dataset folder: {d.folder}")
    print(f"  Datasets: {list(d.datasets.keys())}")

    # Try to access nested datasets
    for name, dataset_info in d.datasets.items():
        print(f"\n  Checking dataset '{name}':")
        print(f"    Class: {dataset_info.get('class', 'N/A')}")
        print(f"    JSON path: {dataset_info.get('json', 'N/A')}")

        # If it's an AudioDataset, try to load it directly
        if dataset_info.get('class') == 'AudioDataset':
            try:
                json_path = dataset_info['json']
                print(f"    Attempting to load AudioDataset from: {json_path}")
                audio_ds = AudioDataset.from_json(Path(json_path))
                print(f"    ✓ Successfully loaded AudioDataset")
                print(f"      Audio dataset name: {audio_ds.name}")
                print(f"      Audio dataset folder: {audio_ds.folder}")
            except KeyError as e:
                print(f"    ✗ KeyError loading AudioDataset: {e}")
                print(f"    This is the error the user is seeing!")

                # Try to read the JSON file directly to see its structure
                import json
                with open(json_path, 'r') as f:
                    content = json.load(f)
                print(f"    JSON file keys: {list(content.keys())}")
                if 'data' in content:
                    print(f"    ✓ 'data' field exists in JSON")
                    print(f"      Number of data entries: {len(content['data'])}")
                else:
                    print(f"    ✗ 'data' field is MISSING from JSON")
            except Exception as e:
                print(f"    ✗ Error loading AudioDataset: {type(e).__name__}: {e}")

except Exception as e:
    print(f"✗ Error loading dataset: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n{'='*60}")
print(f"Test completed")
print(f"{'='*60}")
