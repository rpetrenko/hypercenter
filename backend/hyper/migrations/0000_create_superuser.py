import os
from django.db import migrations
from django.utils import timezone
from django.contrib.auth.models import User


def createsuperuser(apps, schema_editor):
    username = os.environ['SUPERUSER']
    password = os.environ['SUPERPASS']
    User.objects.create_superuser(username,
                                  password=password,
                                  last_login=timezone.now()
                                  )


class Migration(migrations.Migration):
    operations = [migrations.RunPython(createsuperuser)]
