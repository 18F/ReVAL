from django.test import SimpleTestCase
from unittest.mock import patch

from data_ingest.api_views import reorder_csv, to_tabular


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

    @patch('data_ingest.api_views.get_ordered_headers')
    def test_reorder_csv(self, mock_headers):
        mock_headers.return_value = ['c', 'a', 'b']
        data = {'source': b'a,b,c\n1,2,3\n4,5,6\n'}
        self.assertEqual({'source': b'c,a,b\r\n3,1,2\r\n6,4,5\r\n'}, reorder_csv(data))

        data = {'source': b''}
        self.assertEqual({'source': b''}, reorder_csv(data))
