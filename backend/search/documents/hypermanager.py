from django_elasticsearch_dsl import (
    Document,
    fields,
    Index,
)
from django_elasticsearch_dsl_drf.compat import KeywordField, StringField
from django.conf import settings
from hyper.models import HyperManager


INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES[__name__])


@INDEX.doc_type
class HyperManagerDocument(Document):
    id = fields.IntegerField()
    name = KeywordField()
    url = fields.KeywordField()
    online = fields.BooleanField()
    version = fields.KeywordField()

    class Django(object):
        model = HyperManager
