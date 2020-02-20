import json_logic
import jsonschema

from .validator import Validator, ValidatorOutput, UnsupportedContentTypeException
from .rowwise import RowwiseValidator


class JsonlogicValidator(RowwiseValidator):
    def evaluate(self, rule, row):
        return json_logic.jsonLogic(rule, row)


class JsonlogicValidatorFailureConditions(JsonlogicValidator):
    """
    Like JsonlogicValidator, but rules express failure conditions, not success
    """

    INVERT_LOGIC = True


class JsonschemaValidator(Validator):
    def validate(self, source, content_type):
        if content_type != "application/json":
            raise UnsupportedContentTypeException(content_type, type(self).__name__)

        # Find the correct version of the validator to use for this schema
        json_validator = jsonschema.validators.validator_for(self.validator)(
            self.validator
        )

        # Check the schema to make sure there's no error
        json_validator.check_schema(self.validator)

        if type(source) is list:  # validating an array (list) of objects
            output = ValidatorOutput(source)
        else:  # validating only one object but making it a list of objects
            output = ValidatorOutput([source])

        errors = json_validator.iter_errors(source)

        for error in errors:
            if error.path:
                output.add_row_error(
                    error.path[0],
                    "Error",
                    error.validator,
                    error.message,
                    list(error.path)[1:],
                )
            else:
                output.add_row_error(0, "Error", error.validator, error.message, [])

        return output.get_output()
