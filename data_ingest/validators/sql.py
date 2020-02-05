
from .rowwise import RowwiseValidator

class SqlValidator(RowwiseValidator):

    def __init__(self, *args, **kwargs):

        self.db = sqlite3.connect(':memory:')
        self.db_cursor = self.db.cursor()
        return super().__init__(*args, **kwargs)

    def first_statement_only(self, sql):
        'Discard any second sql statement, just as from a sql injection'

        # Very simplistic SQL injection protection, but the attack would
        # have to come from the rule-writer, and the database contains no
        # data anyway
        return sql.split(';')[0]

    def evaluate(self, rule, row):
        if not rule:
            return True  # rule not implemented

        aliases = [' ? as {} '.format(col_name) for col_name in row.keys()]
        aliases = ','.join(aliases)

        sql = f"select {rule} from ( select {aliases} )"
        sql = self.first_statement_only(sql)

        cvalues = SqlValidator.cast_values(row.values())

        self.db_cursor.execute(sql, tuple(cvalues))
        result = self.db_cursor.fetchone()[0]

        return bool(result)


class SqlValidatorFailureConditions(SqlValidator):
    """
    Like SqlValidator, but rules express failure conditions, not success
    """

    INVERT_LOGIC = True
