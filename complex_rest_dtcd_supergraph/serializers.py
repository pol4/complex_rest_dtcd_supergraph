"""
Custom DRF serializers.
"""

from itertools import chain
from operator import itemgetter

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .fields import EdgeField, VertexField
from .models import Fragment
from .settings import SCHEMA


class FragmentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, source="__primaryvalue__")
    name = serializers.CharField(max_length=255)  # TODO value in settings

    def create(self, validated_data) -> Fragment:
        """Construct local fragment instance."""
        return Fragment(**validated_data)

    def update(self, instance, validated_data):
        """Update local fragment instance."""
        instance.name = validated_data["name"]
        return instance

    def save(self, **kwargs) -> Fragment:
        """Create or update local fragment instance."""
        return super().save(**kwargs)


class ContentSerializer(serializers.Serializer):
    default_error_messages = {
        "does_not_exist": _("An entity with id [{value}] does not exist."),
        "not_unique": _("Data contains non-unique, duplicated IDs."),
    }

    nodes = serializers.ListField(child=VertexField(), allow_empty=False)
    edges = serializers.ListField(child=EdgeField())

    def validate(self, data: dict):
        self._validate_unique_nodes(data)
        self._validate_unique_edges(data)
        self._validate_references(data)
        return data

    @staticmethod
    def _node_ids(data: dict):
        nodes = data.get(SCHEMA["keys"]["nodes"], [])
        id_key = SCHEMA["keys"]["yfiles_id"]
        return set(map(itemgetter(id_key), nodes))

    @staticmethod
    def _edge_ids(data: dict):
        edges = data[SCHEMA["keys"]["edges"]]
        src_node_key = SCHEMA["keys"]["source_node"]
        tgt_node_key = SCHEMA["keys"]["target_node"]
        src_port_key = SCHEMA["keys"]["source_port"]
        tgt_port_key = SCHEMA["keys"]["target_port"]
        keys = (
            src_node_key,
            tgt_node_key,
            src_port_key,
            tgt_port_key,
        )

        return set(map(itemgetter(*keys), edges))

    def _validate_unique_nodes(self, data: dict):
        nodes = data[SCHEMA["keys"]["nodes"]]
        ids = self._node_ids(data)

        if len(ids) != len(nodes):
            self.fail("not_unique")

    def _validate_unique_edges(self, data: dict):
        edges = data[SCHEMA["keys"]["edges"]]
        ids = self._edge_ids(data)

        if len(ids) != len(edges):
            self.fail("not_unique")

    def _validate_references(self, data: dict):
        # for each edge, make sure referred nodes really exist
        node_ids = self._node_ids(data)
        edges = data.get(SCHEMA["keys"]["edges"], [])
        src_node_key = SCHEMA["keys"]["source_node"]
        tgt_node_key = SCHEMA["keys"]["target_node"]

        for id_ in chain.from_iterable(
            map(itemgetter(src_node_key, tgt_node_key), edges)
        ):
            if id_ not in node_ids:
                self.fail("does_not_exist", value=id_)


class GraphSerializer(serializers.Serializer):
    graph = ContentSerializer()
