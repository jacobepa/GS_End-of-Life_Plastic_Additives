# Created on 2023-04-03 15:29
# pylint: skip-file

import os
from django.core import serializers
from django.db import migrations, transaction
from django.db.utils import IntegrityError

fixture_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../fixtures'))
fixture_filename = 'streams.json'

def load_fixture(_apps, _schema_editor):
    """Load data from a fixture when running migrations"""
    fixture_file = os.path.join(fixture_dir, fixture_filename)
    fixture = open(fixture_file, 'rb')
    objects = serializers.deserialize('json', fixture, ignorenonexistent=True)
    for obj in objects:
        try:
            with transaction.atomic():
                obj.save()
        except IntegrityError:
            pass    # Ignore if duplicate obj already exists in db
    fixture.close()

class Migration(migrations.Migration):

    dependencies = [
        ('plastics_eol', '0005_stream_result'),
    ]

    operations = [
        migrations.RunPython(load_fixture),
    ]
