from collections import OrderedDict
from django.test import SimpleTestCase

# This ingest_settings file is imported because there was a weird order that this needs to be imported before
# ingestor so that it will not run into a data_ingest.ingestors.Ingestor not found when importing Ingestor
import data_ingest.ingest_settings  # noqa: F401
from data_ingest.ingestors import RowwiseValidator


class TestRowwiseValidator(SimpleTestCase):
    def test_cast_values(self):
        self.assertEqual(
            RowwiseValidator.cast_values(
                (
                    "1",
                    "3.4",
                    "Test",
                    "Number 1",
                    "123 ",
                    1,
                    2.05,
                    "NaN",
                    "2e3",
                    "-12.0",
                    "-4",
                    "-12.45",
                    "1,230,000",
                )
            ),
            [
                1,
                3.4,
                "Test",
                "Number 1",
                123,
                1,
                2.05,
                "NaN",
                2000,
                -12,
                -4,
                -12.45,
                1230000,
            ],
        )

    def test_replace_message(self):
        message = (
            "{category}: spent/budget: {dollars_spent/ dollars_budgeted} spent+budget: "
            + "{dollars_spent+dollars_budgeted} spent-budget: {dollars_spent-dollars_budgeted} "
            + "spent*budget: {dollars_spent*dollars_budgeted} spent + 4: {dollars_spent + 4} "
            + "20.56 * budget: {20.56 * dollars_budgeted} 12.56 / budget: {12.56 / dollars_budgeted:4}"
        )

        row_dict = OrderedDict(
            [
                ("category", "red tape"),
                ("dollars_budgeted", "2000"),
                ("dollars_spent", "2300"),
            ]
        )

        exp_result = (
            "red tape: spent/budget: 1.15 spent+budget: 4300 spent-budget: 300 spent*budget: "
            + "4600000 spent + 4: 2304 20.56 * budget: 41120.0 12.56 / budget: 0.0063"
        )
        self.assertEqual(
            RowwiseValidator.replace_message(message, row_dict), exp_result
        )

        message = "{d/b} {category}"
        exp_result = "Unable to evaluate {d/b}"
        self.assertEqual(
            RowwiseValidator.replace_message(message, row_dict), exp_result
        )

        message = "{dollars_budgeted/dollars_spent:}"
        exp_result = "Unable to evaluate {dollars_budgeted/dollars_spent:}"
        self.assertEqual(
            RowwiseValidator.replace_message(message, row_dict), exp_result
        )

        message = "{dollars_spent/dollars_budgeted 123}"
        exp_result = "Unable to evaluate {dollars_spent/dollars_budgeted 123}"
        self.assertEqual(
            RowwiseValidator.replace_message(message, row_dict), exp_result
        )

        message = "{dollars_spent/dollars_budgeted :12}"
        exp_result = "Unable to evaluate {dollars_spent/dollars_budgeted :12}"
        self.assertEqual(
            RowwiseValidator.replace_message(message, row_dict), exp_result
        )

        message = "{dollars_spent/dollars_budgeted:category}"
        exp_result = "Unable to evaluate {dollars_spent/dollars_budgeted:category}"
        self.assertEqual(
            RowwiseValidator.replace_message(message, row_dict), exp_result
        )
