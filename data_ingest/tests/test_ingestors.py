from collections import OrderedDict
from data_ingest.ingestors import row_validation_error, SqlValidator
from django.test import SimpleTestCase


class TestIngestors(SimpleTestCase):

    def test_row_validation_error(self):
        rule = {
                  "code": {
                    "<=": [
                      {
                        "var": "dollars_spent"
                      },
                      {
                        "var": "dollars_budgeted"
                      }
                    ]
                  },
                  "message": "spending should not exceed budget",
                  "columns": [
                    "dollars_spent",
                    "dollars_budgeted"
                  ]
                }
        row_dict = OrderedDict([('category', 'red tape'),
                                ('dollars_budgeted', '2000'),
                                ('dollars_spent', '2300')])

        exp_result = {
            'severity': 'Error',
            'code': None,
            'message': "spending should not exceed budget",
            'error_columns': ['dollars_budgeted', 'dollars_spent']
        }
        self.assertEqual(row_validation_error(rule, row_dict), exp_result)


class TestSqlValidator(SimpleTestCase):
    def test_cast_values(self):
        print("tst")
        self.assertEqual(SqlValidator.cast_values(
            ("1", "3.4", "Test", "Number 1", "123 ", 1, 2.05)),
            [1, 3.4, "Test", "Number 1", 123, 1, 2.05])
