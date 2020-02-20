from django.test import SimpleTestCase
from unittest.mock import patch

from data_ingest.ingestors import SqlValidator, UnsupportedContentTypeException


class TestSqlValidator(SimpleTestCase):
    @patch("data_ingest.ingestors.SqlValidator.__init__")
    def test_validate_unsupported_content_type(self, mock_init):
        mock_init.return_value = None
        stv = SqlValidator("SqlValidator", "filename")
        with self.assertRaisesMessage(
            UnsupportedContentTypeException,
            "Content type pdf is not supported by SqlValidator",
        ):
            stv.validate("fake_source", "pdf")
