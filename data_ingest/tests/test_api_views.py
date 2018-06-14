from data_ingest.api_views import to_tabular
from django.test import SimpleTestCase

class TestJSONtoTable(SimpleTestCase):

    def test_to_tabular(self):
        """
        All observed keys set as headers
        Value index matches header index
        """
        data = [{'col1': 1, "col2": 2, "col4": 4}, {'col1': 1, "col3":3}]
        columns = ["col1", "col2", "col3"]

        result = to_tabular(data)
        for col in columns:
            self.assertIn(col, result[0])

        # Data-value @ index matches column index
        for i, obj in enumerate(data):
            for col, value in obj.items():
                processed_column_index = result[0].index(col)
                self.assertEqual(result[i+1][processed_column_index], value)

