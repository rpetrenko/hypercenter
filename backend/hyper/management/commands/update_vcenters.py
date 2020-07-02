from django.core.management.base import BaseCommand, CommandError
from hyper.data_service.vc_helpers import *
from hyper.data_service.common import generate_obj_ids


class Command(BaseCommand):
    help = 'Update vcenters'

    def add_arguments(self, parser):
        parser.add_argument('--hyper_ids', nargs='+', type=str, default='')

    def handle(self, *args, **options):
        for obj_id in generate_obj_ids(options['hyper_ids'], HyperManager):
            try:
                update_online_status(obj_id)
            except HyperManager.DoesNotExist:
                raise CommandError('HyperManager "%s" does not exist' % obj_id)
            self.stdout.write(self.style.SUCCESS('Successfully updated hypermanager "{}"'.format(obj_id)))
