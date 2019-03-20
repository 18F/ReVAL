from collections import OrderedDict
from data_ingest.ingestors import row_validation_error, RowwiseValidator
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

    def test_row_validation_error_message(self):
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
                  "message": "{category_misspelled}: spent/budget: {dollars_spent/ dollars_budgeted} spent+budget: " +
                             "{dollars_spent+dollars_budgeted} spent-budget: {dollars_spent-dollars_budgeted} " +
                             "spent*budget: {dollars_spent*dollars_budgeted} {d/b}",
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
            'message': "{category_misspelled}: spent/budget: 1.15 spent+budget: 4300 spent-budget: 300 spent*budget: " +
                       "4600000 {d/b}",
            'error_columns': ['dollars_budgeted', 'dollars_spent']
        }
        self.assertEqual(row_validation_error(rule, row_dict), exp_result)


class TestRowwiseValidator(SimpleTestCase):
    def test_cast_values(self):
        self.assertEqual(RowwiseValidator.cast_values(
            ("1", "3.4", "Test", "Number 1", "123 ", 1, 2.05, "NaN", "2e3", "-12.0", "-4", "-12.45", "1,230,000")),
            [1, 3.4, "Test", "Number 1", 123, 1, 2.05, "NaN", 2000, -12, -4, -12.45, 1230000])
