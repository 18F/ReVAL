from collections import OrderedDict
from django.test import SimpleTestCase

# This ingest_settings file is imported because there was a weird order that this needs to be imported before
# ingestor so that it will not run into a data_ingest.ingestors.Ingestor not found when importing Ingestor
import data_ingest.ingest_settings
from data_ingest.ingestors import ValidatorOutput


class TestValidationOutput(SimpleTestCase):
    def test_add_row_error(self):
        output = ValidatorOutput(
            [
                (1, {"column1": "abc", "column2": "efg", "column3": "hij"}),
                (2, {"column1": "xyz", "column2": "klm", "column3": "nop"}),
            ],
            headers=["column1", "column2", "column3"],
        )

        output.add_row_error(
            1, "Error", "E12", "Incorrect data", ["column1", "column3"]
        )
        self.assertEqual(len(output.row_errors.items()), 1)
        self.assertEqual(len(output.row_errors[1]), 1)
        self.assertDictEqual(
            output.row_errors[1][0],
            {
                "severity": "Error",
                "code": "E12",
                "message": "Incorrect data",
                "fields": ["column1", "column3"],
            },
        )

        output.add_row_error(1, "Warning", "W20", "Incorrect type", ["column2"])
        self.assertEqual(len(output.row_errors.items()), 1)
        self.assertEqual(len(output.row_errors[1]), 2)
        self.assertDictEqual(
            output.row_errors[1][1],
            {
                "severity": "Warning",
                "code": "W20",
                "message": "Incorrect type",
                "fields": ["column2"],
            },
        )

        output.add_row_error(2, "Info", "I30", "Information", [])
        self.assertEqual(len(output.row_errors.items()), 2)
        self.assertEqual(len(output.row_errors[2]), 1)
        self.assertDictEqual(
            output.row_errors[2][0],
            {"severity": "Info", "code": "I30", "message": "Information", "fields": []},
        )

    def test_create_rows(self):
        output = ValidatorOutput(
            OrderedDict(
                [
                    (1, {"column1": "abc", "column2": "efg", "column3": "hij"}),
                    (2, {"column1": "xyz", "column2": "klm", "column3": "nop"}),
                ]
            ),
            headers=["column1", "column2", "column3"],
        )

        output.row_errors = {
            1: [
                {
                    "severity": "Error",
                    "code": "E12",
                    "message": "Incorrect data",
                    "fields": ["column1", "column3"],
                },
                {
                    "severity": "Warning",
                    "code": "W20",
                    "message": "Incorrect type",
                    "fields": ["column2"],
                },
            ],
            2: [
                {
                    "severity": "Info",
                    "code": "I30",
                    "message": "Information",
                    "fields": [],
                }
            ],
        }

        rows = output.create_rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rows[0]), 3)
        self.assertEqual(rows[0]["row_number"], 1)
        self.assertEqual(len(rows[0]["errors"]), 2)
        self.assertDictEqual(
            rows[0]["errors"][0],
            {
                "severity": "Error",
                "code": "E12",
                "message": "Incorrect data",
                "fields": ["column1", "column3"],
            },
        )
        self.assertDictEqual(
            rows[0]["errors"][1],
            {
                "severity": "Warning",
                "code": "W20",
                "message": "Incorrect type",
                "fields": ["column2"],
            },
        )
        self.assertDictEqual(
            rows[0]["data"], {"column1": "abc", "column2": "efg", "column3": "hij"}
        )

        self.assertEqual(len(rows[1]), 3)
        self.assertEqual(rows[1]["row_number"], 2)
        self.assertEqual(len(rows[1]["errors"]), 1)
        self.assertDictEqual(
            rows[1]["errors"][0],
            {"severity": "Info", "code": "I30", "message": "Information", "fields": []},
        )
        self.assertDictEqual(
            rows[1]["data"], {"column1": "xyz", "column2": "klm", "column3": "nop"}
        )

    def test_get_output(self):
        output = ValidatorOutput(
            OrderedDict(
                [
                    (1, {"column1": "abc", "column2": "efg", "column3": "hij"}),
                    (2, {"column1": "xyz", "column2": "klm", "column3": "nop"}),
                ]
            ),
            headers=["column1", "column2", "column3"],
        )

        output.row_errors = {
            1: [
                {
                    "severity": "Error",
                    "code": "E12",
                    "message": "Incorrect data",
                    "fields": ["column1", "column3"],
                },
                {
                    "severity": "Warning",
                    "code": "W20",
                    "message": "Incorrect type",
                    "fields": ["column2"],
                },
            ],
            2: [
                {
                    "severity": "Info",
                    "code": "I30",
                    "message": "Information",
                    "fields": [],
                }
            ],
        }

        result = output.get_output()

        self.assertEqual(len(result["tables"][0]), 5)
        self.assertEqual(
            result["tables"][0]["headers"], ["column1", "column2", "column3"]
        )
        self.assertEqual(result["tables"][0]["whole_table_errors"], [])
        # This should probably be mocked
        # self.assertEqual(result["rows"], )
        self.assertEqual(result["tables"][0]["valid_row_count"], 0)
        self.assertEqual(result["tables"][0]["invalid_row_count"], 2)

        self.assertEqual(result["valid"], False)

        # No row errors but have whole table errors
        output1 = ValidatorOutput(
            OrderedDict(
                [
                    (1, {"column1": "abc", "column2": "efg", "column3": "hij"}),
                    (2, {"column1": "xyz", "column2": "klm", "column3": "nop"}),
                ]
            ),
            headers=["column1", "column2", "column3"],
        )
        output1.whole_table_errors = [
            {
                "severity": "Error",
                "code": "E12",
                "message": "Incorrect data",
                "fields": ["column1", "column3"],
            }
        ]

        result1 = output1.get_output()

        self.assertEqual(len(result1["tables"][0]), 5)
        self.assertEqual(
            result1["tables"][0]["headers"], ["column1", "column2", "column3"]
        )
        self.assertEqual(
            result1["tables"][0]["whole_table_errors"],
            [
                {
                    "severity": "Error",
                    "code": "E12",
                    "message": "Incorrect data",
                    "fields": ["column1", "column3"],
                }
            ],
        )
        # This should probably be mocked
        # self.assertEqual(result["rows"], )
        self.assertEqual(result1["tables"][0]["valid_row_count"], 2)
        self.assertEqual(result1["tables"][0]["invalid_row_count"], 0)

        # This should still be False
        self.assertEqual(result1["valid"], False)

    def test_combine(self):
        self.assertEqual(data_ingest.ingestors.ValidatorOutput.combine({}, {}), {})

        output1 = {
            "valid": False,
            "tables": [
                {
                    "headers": ["a", "b", "c"],
                    "rows": [
                        {
                            "row_number": 2,
                            "errors": [],
                            "data": {"a": 1, "b": 2, "c": 3},
                        },
                        {
                            "row_number": 3,
                            "errors": [
                                {
                                    "severity": "Error",
                                    "code": "4E",
                                    "message": "Incorrect type",
                                    "fields": ["b"],
                                },
                                {
                                    "severity": "Error",
                                    "code": "9E",
                                    "message": "Incorrect range",
                                    "fields": ["c"],
                                },
                            ],
                            "data": {"a": 4, "b": 5, "c": 6},
                        },
                    ],
                    "whole_table_errors": [
                        {
                            "severity": "Error",
                            "code": "12",
                            "message": "Incorrect form",
                            "fields": ["a"],
                        }
                    ],
                    "valid_row_count": 1,
                    "invalid_row_count": 1,
                }
            ],
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
                                    "fields": ["a", "b"],
                                }
                            ],
                            "data": {"a": 1, "b": 2, "c": 3},
                        },
                        {
                            "row_number": 3,
                            "errors": [
                                {
                                    "severity": "Error",
                                    "code": "70E",
                                    "message": "c cannot be 6",
                                    "fields": ["c"],
                                },
                                {
                                    "severity": "Warning",
                                    "code": "20W",
                                    "message": "Incorrect range",
                                    "fields": ["c"],
                                },
                            ],
                            "data": {"a": 4, "b": 5, "c": 6},
                        },
                    ],
                    "whole_table_errors": [
                        {
                            "severity": "Error",
                            "code": "40",
                            "message": "structure issue",
                            "fields": ["a", "b"],
                        }
                    ],
                    "valid_row_count": 0,
                    "invalid_row_count": 2,
                }
            ],
        }

        exp_result = {
            "tables": [
                {
                    "headers": ["a", "b", "c"],
                    "whole_table_errors": [
                        {
                            "severity": "Error",
                            "code": "12",
                            "message": "Incorrect form",
                            "fields": ["a"],
                        },
                        {
                            "severity": "Error",
                            "code": "40",
                            "message": "structure issue",
                            "fields": ["a", "b"],
                        },
                    ],
                    "rows": [
                        {
                            "row_number": 2,
                            "errors": [
                                {
                                    "severity": "Error",
                                    "code": "14E",
                                    "message": "a is smaller than b",
                                    "fields": ["a", "b"],
                                }
                            ],
                            "data": {"a": 1, "b": 2, "c": 3},
                        },
                        {
                            "row_number": 3,
                            "errors": [
                                {
                                    "severity": "Error",
                                    "code": "4E",
                                    "message": "Incorrect type",
                                    "fields": ["b"],
                                },
                                {
                                    "severity": "Error",
                                    "code": "9E",
                                    "message": "Incorrect range",
                                    "fields": ["c"],
                                },
                                {
                                    "severity": "Error",
                                    "code": "70E",
                                    "message": "c cannot be 6",
                                    "fields": ["c"],
                                },
                                {
                                    "severity": "Warning",
                                    "code": "20W",
                                    "message": "Incorrect range",
                                    "fields": ["c"],
                                },
                            ],
                            "data": {"a": 4, "b": 5, "c": 6},
                        },
                    ],
                    "valid_row_count": 0,
                    "invalid_row_count": 2,
                }
            ],
            "valid": False,
        }
        result = ValidatorOutput.combine(output1, output2)
        self.assertDictEqual(exp_result, result)

        # only whole table errors
        output3 = {
            "valid": False,
            "tables": [
                {
                    "headers": ["a", "b", "c"],
                    "rows": [
                        {
                            "row_number": 2,
                            "errors": [],
                            "data": {"a": 1, "b": 2, "c": 3},
                        },
                        {
                            "row_number": 3,
                            "errors": [],
                            "data": {"a": 4, "b": 5, "c": 6},
                        },
                    ],
                    "whole_table_errors": [
                        {
                            "severity": "Error",
                            "code": "12",
                            "message": "Incorrect form",
                            "fields": ["a"],
                        }
                    ],
                    "valid_row_count": 2,
                    "invalid_row_count": 0,
                }
            ],
        }
        output4 = {
            "valid": False,
            "tables": [
                {
                    "headers": ["a", "b", "c"],
                    "rows": [
                        {
                            "row_number": 2,
                            "errors": [],
                            "data": {"a": 1, "b": 2, "c": 3},
                        },
                        {
                            "row_number": 3,
                            "errors": [],
                            "data": {"a": 4, "b": 5, "c": 6},
                        },
                    ],
                    "whole_table_errors": [
                        {
                            "severity": "Error",
                            "code": "40",
                            "message": "structure issue",
                            "fields": ["a", "b"],
                        }
                    ],
                    "valid_row_count": 2,
                    "invalid_row_count": 0,
                }
            ],
        }
        exp_result1 = {
            "tables": [
                {
                    "headers": ["a", "b", "c"],
                    "whole_table_errors": [
                        {
                            "severity": "Error",
                            "code": "12",
                            "message": "Incorrect form",
                            "fields": ["a"],
                        },
                        {
                            "severity": "Error",
                            "code": "40",
                            "message": "structure issue",
                            "fields": ["a", "b"],
                        },
                    ],
                    "rows": [
                        {
                            "row_number": 2,
                            "errors": [],
                            "data": {"a": 1, "b": 2, "c": 3},
                        },
                        {
                            "row_number": 3,
                            "errors": [],
                            "data": {"a": 4, "b": 5, "c": 6},
                        },
                    ],
                    "valid_row_count": 2,
                    "invalid_row_count": 0,
                }
            ],
            "valid": False,
        }
        result1 = ValidatorOutput.combine(output3, output4)
        self.assertDictEqual(exp_result1, result1)
