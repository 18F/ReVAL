from django.test import SimpleTestCase
from unittest.mock import patch

from data_ingest.utils import get_schema_headers, get_ordered_headers


class TestUtils(SimpleTestCase):

    @patch("data_ingest.utils.UPLOAD_SETTINGS",
           {
            'STREAM_ARGS': {'headers': ["a", "b", "c"]},
            'VALIDATORS': {None: 'data_ingest.ingestors.GoodtablesValidator', }, })
    def test_get_schema_headers_in_settings(self):
        self.assertEqual(["a", "b", "c"], get_schema_headers())

    @patch("data_ingest.utils.UPLOAD_SETTINGS",
           {
            'STREAM_ARGS': {'headers': 1},
            'VALIDATORS': {'schema.json': 'data_ingest.ingestors.GoodtablesValidator', }, })
    @patch("data_ingest.ingestors.Validator.get_validator_contents")
    def test_get_schema_headers_in_schema(self, mock_content):
        mock_content.return_value = {
                                      "fields": [
                                        {
                                          "name": "test 1",
                                          "title": "Test 1 field",
                                          "type": "string",
                                          "description": "Test 1 Field"
                                        },
                                        {
                                          "name": "test 2",
                                          "title": "Test 2 field",
                                          "type": "integer",
                                          "description": "Test 2 Field"
                                        }
                                      ]
                                    }
        self.assertEqual(["test 1", "test 2"], get_schema_headers())

    @patch("data_ingest.utils.get_schema_headers")
    def test_get_ordered_headers(self, mock_sch_headers):
        mock_sch_headers.return_value = ["a", "b", "c"]
        self.assertEqual(["a", "b", "c", "e"], get_ordered_headers(["c", "a", "e", "b"]))
        self.assertEqual(["b", "c", "e"], get_ordered_headers(["e", "c", "b"]))
        self.assertEqual(["e", "f"], get_ordered_headers(["e", "f"]))
        self.assertEqual([], get_ordered_headers([]))
        self.assertEqual(["a", "b", "c"], get_ordered_headers(["a", "b", "c"]))
