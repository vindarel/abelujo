# -*- coding: utf-8 -*-


from django.db import models, migrations

def remove_scraper_cache(apps, schema_director):
    """Remove all cache.sqlite files.
    Needed when moving the scrapers module up to bookshops/
    """
    import os
    # Commented out after all migrations on server done.
    # Will run with django tests !
    # os.system("make clean-caches")

class Migration(migrations.Migration):

    dependencies = [
        ('search', '0018_auto_20160412_1451'),
    ]

    operations = [
        # migrations.RunPython(remove_scraper_cache),
    ]
