from django.test import SimpleTestCase
from unittest.mock import patch, mock_open
from json import dumps

# This ingest_settings file is imported because there was a weird order that this needs to be imported before
# ingestor so that it will not run into a data_ingest.ingestors.Ingestor not found when importing Ingestor
import data_ingest.ingest_settings
from data_ingest.ingestors import (
    GoodtablesValidator,
    UnsupportedContentTypeException,
)


class TestGoodtablesValidator(SimpleTestCase):
    @patch("data_ingest.ingestors.GoodtablesValidator.__init__")
    def test_validate_unsupported_content_type(self, mock_init):
        mock_init.return_value = None
        gtv = GoodtablesValidator("GoodtablesValidator", "filename")
        with self.assertRaisesMessage(
            UnsupportedContentTypeException,
            "Content type pdf is not supported by GoodtablesValidator",
        ):
            gtv.validate("fake_source", "pdf")

    csv_rule = dumps(
        {
            "fields": [
                {"name": "category"},
                {"name": "dollars_budgeted"},
                {"name": "dollars_spent"},
            ]
        }
    )

    @patch("builtins.open", new_callable=mock_open, read_data=csv_rule)
    def test_validate_extra_columns(self, mock_file):
        gtv = GoodtablesValidator("GoodtablesValidator", "mocked_filename.csv")
        data = {
            "source": b"category,dollars_budgeted,dollars_spent,extra1,extra2\npencils,1,500,2,400",
            "format": "csv",
            "headers": 1,
        }
        results = gtv.validate(data, "text/csv")
        errors = results["tables"][0]["whole_table_errors"]
        messages = [error["message"] for error in errors]
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], "There is an extra header in column 4 (extra1)")
        self.assertEqual(messages[1], "There is an extra header in column 5 (extra2)")
