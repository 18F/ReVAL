from django.test import SimpleTestCase
from unittest.mock import patch

from data_ingest.utils import (
  get_schema_headers, 
  get_ordered_headers,
  reorder_csv,
  to_tabular
)

class TestUtils(SimpleTestCase):

    def test_get_schema_headers_in_settings(self):
        self.assertEqual([], get_schema_headers())

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

    @patch("data_ingest.utils.UPLOAD_SETTINGS",
           {
            'STREAM_ARGS': {'headers': ["a", "b", "c"]},
            'VALIDATORS': {None: 'data_ingest.ingestors.GoodtablesValidator', }, })
    def test_get_ordered_headers_in_settings(self):
        self.assertEqual(["a", "b", "c"], get_ordered_headers(["$a", "$b"]))

    @patch("data_ingest.utils.get_schema_headers")
    def test_get_ordered_headers(self, mock_sch_headers):
        mock_sch_headers.return_value = ["a", "b", "c"]
        self.assertEqual(["a", "b", "c", "e"], get_ordered_headers(["c", "a", "e", "b"]))
        self.assertEqual(["b", "c", "e"], get_ordered_headers(["e", "c", "b"]))
        self.assertEqual(["e", "f"], get_ordered_headers(["e", "f"]))
        self.assertEqual([], get_ordered_headers([]))
        self.assertEqual(["a", "b", "c"], get_ordered_headers(["a", "b", "c"]))

class TestJSONtoTable(SimpleTestCase):

    def test_to_tabular(self):
        """
        All observed keys set as headers
        Value index matches header index
        """
        data = [{'col1': 1, "col2": 2, "col4": 4}, {'col1': 1, "col3": 3}]
        columns = ["col1", "col2", "col3"]

        result = to_tabular(data)
        for col in columns:
            self.assertIn(col, result[0])

        # Data-value @ index matches column index
        for i, obj in enumerate(data):
            for col, value in obj.items():
                processed_column_index = result[0].index(col)
                self.assertEqual(result[i+1][processed_column_index], value)


class TestReorderCSV(SimpleTestCase):

    @patch('data_ingest.utils.get_ordered_headers')
    def test_reorder_csv(self, mock_headers):
        mock_headers.return_value = ['c', 'a', 'b']
        data = {'source': b'a,b,c\n1,2,3\n4,5,6\n'}
        self.assertEqual({'source': b'c,a,b\n3,1,2\n6,4,5\n'}, reorder_csv(data))

        data = {}
        self.assertEqual({}, reorder_csv(data))

        data = {'source': b''}
        self.assertEqual({'source': b''}, reorder_csv(data))

        data = {'source': b'a,b,c\n,\n\n1,2,3\n4,5,\n'}
        self.assertEqual({'source': b'c,a,b\n,,\n,,\n3,1,2\n,4,5\n'}, reorder_csv(data))

        data = {'source': b'a,b,c\n1,2,3,4\n5,6,7,8'}
        self.assertEqual({'source': b'c,a,b\n3,1,2,4\n7,5,6,8\n'}, reorder_csv(data))

        data = {'source': b'a,c\n1,2,3,4\n5,6,7,8'}
        self.assertEqual({'source': b'c,a,b\n2,1,,3,4\n6,5,,7,8\n'}, reorder_csv(data))

        with patch('data_ingest.utils.UPLOAD_SETTINGS',
                   {'STREAM_ARGS': {'headers': ['c', 'a', 'b']}}):
            data = {'source': b'$q,$r,$e\n1,2,3\n4,5,6\n'}
            self.assertEqual({'source': b'c,a,b\n1,2,3\n4,5,6\n'}, reorder_csv(data))

