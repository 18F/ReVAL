from collections import OrderedDict
from data_ingest.ingestors import RowwiseValidator, ValidatorOutput
from django.test import SimpleTestCase


class TestRowwiseValidator(SimpleTestCase):
    def test_cast_values(self):
        self.assertEqual(RowwiseValidator.cast_values(
            ("1", "3.4", "Test", "Number 1", "123 ", 1, 2.05, "NaN", "2e3", "-12.0", "-4", "-12.45", "1,230,000")),
            [1, 3.4, "Test", "Number 1", 123, 1, 2.05, "NaN", 2000, -12, -4, -12.45, 1230000])

    def test_replace_message(self):
        message = "{category}: spent/budget: {dollars_spent/ dollars_budgeted} spent+budget: " + \
                   "{dollars_spent+dollars_budgeted} spent-budget: {dollars_spent-dollars_budgeted} " + \
                   "spent*budget: {dollars_spent*dollars_budgeted} spent + 4: {dollars_spent + 4} " + \
                   "20.56 * budget: {20.56 * dollars_budgeted} 12.56 / budget: {12.56 / dollars_budgeted:4}"

        row_dict = OrderedDict([('category', 'red tape'),
                                ('dollars_budgeted', '2000'),
                                ('dollars_spent', '2300')])

        exp_result = "red tape: spent/budget: 1.15 spent+budget: 4300 spent-budget: 300 spent*budget: " + \
                     "4600000 spent + 4: 2304 20.56 * budget: 41120.0 12.56 / budget: 0.0063"
        self.assertEqual(RowwiseValidator.replace_message(message, row_dict), exp_result)

        message = "{d/b} {category}"
        exp_result = 'Unable to evaluate {d/b}'
        self.assertEqual(RowwiseValidator.replace_message(message, row_dict), exp_result)

        message = "{dollars_budgeted/dollars_spent:}"
        exp_result = 'Unable to evaluate {dollars_budgeted/dollars_spent:}'
        self.assertEqual(RowwiseValidator.replace_message(message, row_dict), exp_result)

        message = "{dollars_spent/dollars_budgeted 123}"
        exp_result = 'Unable to evaluate {dollars_spent/dollars_budgeted 123}'
        self.assertEqual(RowwiseValidator.replace_message(message, row_dict), exp_result)

        message = "{dollars_spent/dollars_budgeted :12}"
        exp_result = 'Unable to evaluate {dollars_spent/dollars_budgeted :12}'
        self.assertEqual(RowwiseValidator.replace_message(message, row_dict), exp_result)

        message = "{dollars_spent/dollars_budgeted:category}"
        exp_result = 'Unable to evaluate {dollars_spent/dollars_budgeted:category}'
        self.assertEqual(RowwiseValidator.replace_message(message, row_dict), exp_result)


class TestValidationOutput(SimpleTestCase):
    def test_add_row_error(self):
        output = ValidatorOutput(
                                 [(1, {"column1": "abc", "column2": "efg", "column3": "hij"}),
                                  (2, {"column1": "xyz", "column2": "klm", "column3": "nop"})],
                                  headers=["column1", "column2", "column3"])

        output.add_row_error(1, "Error", "E12", "Incorrect data", ["column1", "column3"])
        self.assertEqual(len(output.row_errors.items()), 1)
        self.assertEqual(len(output.row_errors[1]), 1)
        self.assertDictEqual(output.row_errors[1][0], {"severity": "Error", "code": "E12",
                                                       "message": "Incorrect data",
                                                       "error_columns": ["column1", "column3"]})

        output.add_row_error(1, "Warning", "W20", "Incorrect type", ["column2"])
        self.assertEqual(len(output.row_errors.items()), 1)
        self.assertEqual(len(output.row_errors[1]), 2)
        self.assertDictEqual(output.row_errors[1][1], {"severity": "Warning", "code": "W20",
                                                       "message": "Incorrect type", "error_columns": ["column2"]})

        output.add_row_error(2, "Info", "I30", "Information", [])
        self.assertEqual(len(output.row_errors.items()), 2)
        self.assertEqual(len(output.row_errors[2]), 1)
        self.assertDictEqual(output.row_errors[2][0],
                             {"severity": "Info", "code": "I30", "message": "Information", "error_columns": []})

    def test_create_rows(self):
        output = ValidatorOutput(
                                 OrderedDict([(1, {"column1": "abc", "column2": "efg", "column3": "hij"}),
                                              (2, {"column1": "xyz", "column2": "klm", "column3": "nop"})]),
                                 headers=["column1", "column2", "column3"])

        output.row_errors = {
            1: [{'severity': 'Error', 'code': 'E12', 'message': 'Incorrect data',
                 'error_columns': ['column1', 'column3']},
                {'severity': 'Warning', 'code': 'W20', 'message': 'Incorrect type', 'error_columns': ['column2']}],
            2: [{'severity': 'Info', 'code': 'I30', 'message': 'Information', 'error_columns': []}]
        }

        rows = output.create_rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rows[0]), 3)
        self.assertEqual(rows[0]["row_number"], 1)
        self.assertEqual(len(rows[0]["errors"]), 2)
        self.assertDictEqual(rows[0]["errors"][0], {'severity': 'Error', 'code': 'E12', 'message': 'Incorrect data',
                                                    'error_columns': ['column1', 'column3']})
        self.assertDictEqual(rows[0]["errors"][1], {'severity': 'Warning', 'code': 'W20', 'message': 'Incorrect type',
                                                    'error_columns': ['column2']})
        self.assertDictEqual(rows[0]["data"], {"column1": "abc", "column2": "efg", "column3": "hij"})

        self.assertEqual(len(rows[1]), 3)
        self.assertEqual(rows[1]["row_number"], 2)
        self.assertEqual(len(rows[1]["errors"]), 1)
        self.assertDictEqual(rows[1]["errors"][0], {'severity': 'Info', 'code': 'I30', 'message': 'Information',
                                                    'error_columns': []})
        self.assertDictEqual(rows[1]["data"], {"column1": "xyz", "column2": "klm", "column3": "nop"})

    def test_get_output(self):
        output = ValidatorOutput(
                                 OrderedDict([(1, {"column1": "abc", "column2": "efg", "column3": "hij"}),
                                              (2, {"column1": "xyz", "column2": "klm", "column3": "nop"})]),
                                 headers=["column1", "column2", "column3"],)

        output.row_errors = {
            1: [{'severity': 'Error', 'code': 'E12', 'message': 'Incorrect data',
                 'error_columns': ['column1', 'column3']},
                {'severity': 'Warning', 'code': 'W20', 'message': 'Incorrect type', 'error_columns': ['column2']}],
            2: [{'severity': 'Info', 'code': 'I30', 'message': 'Information', 'error_columns': []}]
        }

        result = output.get_output()

        self.assertEqual(len(result["tables"][0]), 5)
        self.assertEqual(result["tables"][0]["headers"], ["column1", "column2", "column3"])
        self.assertEqual(result["tables"][0]["whole_table_errors"], [])
        # This should probably be mocked
        # self.assertEqual(result["rows"], )
        self.assertEqual(result["tables"][0]["valid_row_count"], 0)
        self.assertEqual(result["tables"][0]["invalid_row_count"], 2)

        self.assertEqual(result["valid"], False)

    def test_combine(self):
        self.assertEqual(ValidatorOutput.combine({}, {}), {})

        output1 = {
            "valid": False,
            "tables": [
                {
                    "headers": ["a", "b", "c"],
                    "rows": [
                        {
                            "row_number": 2,
                            "errors": [],
                            "data": {"a": 1, "b": 2, "c": 3}
                        },
                        {
                            "row_number": 3,
                            "errors": [
                                {
                                    "severity": "Error",
                                    "code": "4E",
                                    "message": "Incorrect type",
                                    "error_columns": ["b"]
                                },
                                {
                                    "severity": "Error",
                                    "code": "9E",
                                    "message": "Incorrect range",
                                    "error_columns": ["c"]
                                }
                            ],
                            "data": {"a": 4, "b": 5, "c": 6}
                        }
                    ],
                    "whole_table_errors": [
                        {
                            "severity": "Error",
                            "code": "12",
                            "message": "Incorrect form",
                            "error_columns": ["a"]
                        }
                    ],
                    "valid_row_count": 1,
                    "invalid_row_count": 1,
                }
            ]
        }

        output2 = {
            "valid": False,
            "tables": [
                {
                    "headers": ["a", "b", "c"],
                    "rows": [
                        {
                            "row_number": 2,
                            "errors": [
                                {
                                    "severity": "Error",
                                    "code": "14E",
                                    "message": "a is smaller than b",
                                    "error_columns": ["a", "b"]
                                }
                            ],
                            "data": {"a": 1, "b": 2, "c": 3}
                        },
                        {
                            "row_number": 3,
                            "errors": [
                                {
                                    "severity": "Error",
                                    "code": "70E",
                                    "message": "c cannot be 6",
                                    "error_columns": ["c"]
                                },
                                {
                                    "severity": "Warning",
                                    "code": "20W",
                                    "message": "Incorrect range",
                                    "error_columns": ["c"]
                                }
                            ],
                            "data": {"a": 4, "b": 5, "c": 6}
                        }
                    ],
                    "whole_table_errors": [
                        {
                            "severity": "Error",
                            "code": "40",
                            "message": "structure issue",
                            "error_columns": ["a", "b"]
                        }
                    ],
                    "valid_row_count": 0,
                    "invalid_row_count": 2,
                }
            ]
        }

        exp_result = {
            'tables': [
                {
                    'headers': ['a', 'b', 'c'],
                    'whole_table_errors': [
                        {'severity': 'Error', 'code': '12', 'message': 'Incorrect form', 'error_columns': ['a']},
                        {'severity': 'Error', 'code': '40', 'message': 'structure issue', 'error_columns': ['a', 'b']}
                    ],
                    'rows': [
                        {
                            'row_number': 2,
                            'errors': [
                                {
                                    'severity': 'Error',
                                    'code': '14E',
                                    'message': 'a is smaller than b',
                                    'error_columns': ['a', 'b']
                                }
                            ],
                            'data': {'a': 1, 'b': 2, 'c': 3}
                        },
                        {
                            'row_number': 3,
                            'errors': [
                                {
                                    'severity': 'Error',
                                    'code': '4E',
                                    'message': 'Incorrect type',
                                    'error_columns': ['b']
                                },
                                {
                                    'severity': 'Error',
                                    'code': '9E',
                                    'message': 'Incorrect range',
                                    'error_columns': ['c']
                                },
                                {
                                    'severity': 'Error',
                                    'code': '70E',
                                    'message': 'c cannot be 6',
                                    'error_columns': ['c']
                                },
                                {
                                    'severity': 'Warning',
                                    'code': '20W',
                                    'message': 'Incorrect range',
                                    'error_columns': ['c']
                                }
                            ],
                            'data': {'a': 4, 'b': 5, 'c': 6}
                        }
                    ],
                    'valid_row_count': 0,
                    'invalid_row_count': 2
                }
            ],
            'valid': False
        }
        result = ValidatorOutput.combine(output1, output2)
        self.assertDictEqual(exp_result, result)
