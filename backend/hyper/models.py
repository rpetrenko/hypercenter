from django.db import models
from django.utils import timezone


class HyperManager(models.Model):
    VCENTER = 'vcenter'
    HYPERV = 'hyperv'
    HYPERMANAGER_CHOICES = [
        (VCENTER, 'Vcenter'),
        (HYPERV, 'HyperV')
    ]
    url = models.CharField(max_length=300)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    hv_type = models.CharField(
        max_length=10,
        choices=HYPERMANAGER_CHOICES,
        default=VCENTER
    )
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=100, default='')
    online = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"

    def update_status(self, online):
        if self.online and not online:
            self.offline_date = timezone.now()
        self.online = online
