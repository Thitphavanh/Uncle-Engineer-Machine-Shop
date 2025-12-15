#!/usr/bin/env python
"""
Script to update slugs for existing Machine instances
Run this script with: python3 update_slugs.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uncleebook.settings')
django.setup()

from machine.models import Machine
from django.utils.text import slugify


def update_slugs():
    """Update slugs for all Machine instances that don't have a slug"""
    machines = Machine.objects.filter(slug__isnull=True) | Machine.objects.filter(slug='')

    if not machines.exists():
        print("All machines already have slugs!")
        return

    print(f"Found {machines.count()} machines without slugs. Updating...")

    for machine in machines:
        base_slug = slugify(machine.title)
        slug = base_slug
        counter = 1

        # Check if slug already exists and create unique slug
        while Machine.objects.filter(slug=slug).exclude(pk=machine.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        machine.slug = slug
        machine.save()
        print(f"✓ Updated: '{machine.title}' -> '{slug}'")

    print(f"\n✅ Successfully updated {machines.count()} machines!")


if __name__ == '__main__':
    update_slugs()
