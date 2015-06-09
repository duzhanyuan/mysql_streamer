# -*- coding: utf-8 -*-
import mock
import pytest

from replication_handler import config
from replication_handler.components.base_event_handler import BaseEventHandler
from replication_handler.components.base_event_handler import Table
from replication_handler.components.stubs import stub_schemas


class TestBaseEventHandler(object):

    @pytest.fixture(scope="class")
    def base_event_handler(self):
        return BaseEventHandler(mock.Mock(), mock.Mock())

    @pytest.fixture
    def table(self):
        return Table(cluster_name="yelp_main", database_name='yelp', table_name='business')

    @pytest.fixture
    def bogus_table(self):
        return Table(cluster_name="yelp_main", database_name='yelp', table_name='bogus_table')

    @pytest.fixture
    def avro_schema(self):
        return '{"type": "record", "namespace": "yelp", "name": "business", "fields": [ \
            {"pkey": true, "type": "int", "name": "id"}, \
            {"default": null, "maxlen": 64, "type": ["null", "string"], "name": "name"}]}'

    @pytest.fixture
    def source(self):
        source = mock.Mock(namespace="yelp")
        source.name = "business"
        return source

    @pytest.fixture
    def topic(self, source):
        topic = mock.Mock(source=source)
        topic.name = "services.datawarehouse.etl.business.0"
        return topic

    @pytest.yield_fixture
    def patch_config(self):
        with mock.patch.object(
            config.DatabaseConfig,
            'cluster_name',
            new_callable=mock.PropertyMock
        ) as mock_cluster_name:
            mock_cluster_name.return_value = "yelp_main"
            yield mock_cluster_name

    @pytest.yield_fixture
    def mock_response(self, avro_schema, topic):
        with mock.patch.object(
            stub_schemas,
            "stub_business_schema"
        ) as mock_response:
            mock_response.return_value = mock.Mock(
                schema_id=0,
                schema=avro_schema,
                topic=topic,
            )
            yield mock_response

    def test_get_schema_for_schema_cache(
        self,
        patch_config,
        base_event_handler,
        table,
        topic,
        mock_response
    ):
        resp = base_event_handler.get_schema_for_schema_cache(table)
        assert resp == base_event_handler.schema_cache[table]
        self._assert_expected_result(resp, topic)

    def test_schema_already_in_cache(self, base_event_handler, table, topic):
        resp = base_event_handler.get_schema_for_schema_cache(table)
        self._assert_expected_result(resp, topic)

    def test_non_existent_table_has_none_response(self, base_event_handler, bogus_table):
        resp = base_event_handler.get_schema_for_schema_cache(bogus_table)
        assert resp is None

    def _assert_expected_result(self, resp, topic):
        assert resp.topic == topic.name
        assert resp.schema_id == 0
        assert resp.schema_obj.name == "business"
        assert resp.schema_obj.fields[0].name == "id"
        assert resp.schema_obj.fields[1].name == "name"

    def test_handle_event_not_implemented(self, base_event_handler):
        with pytest.raises(NotImplementedError):
            base_event_handler.handle_event(mock.Mock(), mock.Mock())