from django.test import SimpleTestCase
from unittest.mock import patch, mock_open
from json import dumps

# This ingest_settings file is imported because there was a weird order that this needs to be imported before
# ingestor so that it will not run into a data_ingest.ingestors.Ingestor not found when importing Ingestor
import data_ingest.ingest_settings
from data_ingest.ingestors import (
    JsonschemaValidator,
    JsonlogicValidator,
    UnsupportedContentTypeException,
)


class TestJsonlogicValidator(SimpleTestCase):

    csv_rule = dumps({"fields": [{"name": "category"},]})

    @patch("builtins.open", new_callable=mock_open, read_data=csv_rule)
    def test_validate_blank_csv(self, mock_file):
        jv = JsonlogicValidator("RowwiseValidator", "mocked_filename.csv")
        data = {
            "source": b"",
            "format": "csv",
            "headers": 1,
        }
        results = jv.validate(data, "text/csv")
        self.assertTrue(results["valid"])


class TestJsonschemaValidator(SimpleTestCase):
    @patch("data_ingest.ingestors.JsonschemaValidator.__init__")
    def test_validate_unsupported_content_type(self, mock_init):
        mock_init.return_value = None
        jtv = JsonschemaValidator("JsonschemaValidator", "filename")
        with self.assertRaisesMessage(
            UnsupportedContentTypeException,
            "Content type pdf is not supported by JsonschemaValidator",
        ):
            jtv.validate("fake_source", "pdf")
