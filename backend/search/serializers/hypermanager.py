from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from search.documents.hypermanager import HyperManagerDocument


class HyperManagerDocumentSerializer(DocumentSerializer):
    class Meta:
        document = HyperManagerDocument
        fields = (
            'id',
            'url',
            'name',
            'online',
            'version',
        )