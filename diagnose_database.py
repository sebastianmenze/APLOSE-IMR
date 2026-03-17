#!/usr/bin/env python
"""
Script to diagnose the current database state and relationships.
Run this to see what's actually in your database.

Usage:
    docker compose --env-file test.env exec osmose_back poetry run python diagnose_database.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from backend.api.models import (
    Dataset,
    SpectrogramAnalysis,
    Spectrogram,
    AnnotationCampaign,
)

def diagnose():
    """Diagnose the current database state"""

    print("=" * 70)
    print("DATABASE DIAGNOSIS")
    print("=" * 70)
    print()

    # Check datasets
    datasets = Dataset.objects.all()
    print(f"📊 Datasets: {datasets.count()}")
    for ds in datasets:
        print(f"   ID: {ds.id}, Name: {ds.name}")
    print()

    # Check analyses
    analyses = SpectrogramAnalysis.objects.all()
    print(f"📈 Analyses: {analyses.count()}")
    for a in analyses:
        print(f"   ID: {a.id}, Name: {a.name}, Dataset: {a.dataset.name}")
    print()

    # Check spectrograms
    spectrograms = Spectrogram.objects.all()
    print(f"🎵 Spectrograms: {spectrograms.count()}")
    for s in spectrograms:
        linked_analyses = s.analysis.all()
        print(f"   ID: {s.id}, Filename: {s.filename}")
        print(f"      Linked to analyses: {[a.id for a in linked_analyses]}")
    print()

    # Check campaigns
    campaigns = AnnotationCampaign.objects.all()
    print(f"📝 Campaigns: {campaigns.count()}")
    for c in campaigns:
        print(f"   ID: {c.id}, Name: {c.name}, Dataset: {c.dataset.name}")
        campaign_analyses = c.analysis.all()
        print(f"      Analysis IDs in campaign: {[a.id for a in campaign_analyses]}")
    print()

    # Check for problems
    print("=" * 70)
    print("CHECKING FOR PROBLEMS")
    print("=" * 70)
    print()

    problems = []

    # Problem 1: Spectrograms not linked to any analysis
    orphan_spectrograms = [s for s in spectrograms if s.analysis.count() == 0]
    if orphan_spectrograms:
        problems.append(f"❌ {len(orphan_spectrograms)} spectrograms not linked to any analysis")
        for s in orphan_spectrograms:
            print(f"   Orphan: Spectrogram ID {s.id} ({s.filename})")

    # Problem 2: Campaigns referencing analyses that don't have spectrograms
    for c in campaigns:
        for a in c.analysis.all():
            spec_count = Spectrogram.objects.filter(analysis=a).count()
            if spec_count == 0:
                problems.append(f"❌ Campaign '{c.name}' references analysis ID {a.id} which has no spectrograms")

    # Problem 3: High ID numbers suggest database wasn't reset
    max_campaign_id = campaigns.order_by('-id').first().id if campaigns.exists() else 0
    if max_campaign_id > 10:
        problems.append(f"⚠️  Campaign IDs are high (max: {max_campaign_id}), database may not have been reset")

    print()
    if problems:
        print("FOUND PROBLEMS:")
        for p in problems:
            print(f"  {p}")
        print()
        print("RECOMMENDATION:")
        print("  Run a complete database reset:")
        print("    docker compose --env-file test.env down -v")
        print("    docker compose --env-file test.env up -d --build")
        print("    # Then run migrations, create superuser, and re-import dataset")
    else:
        print("✅ No problems found!")
        print()
        print("If you're still getting errors, there may be a frontend cache issue.")
        print("Try clearing your browser cache or doing a hard refresh.")

    print()
    print("=" * 70)

if __name__ == '__main__':
    diagnose()
