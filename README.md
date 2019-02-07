# django-data-ingest

`data_ingest` is a reusable Django project managing data submitted as file uploads
to a central
gathering point.  Each file generally contains multiple data rows, and
each user may submit multiple files.

---

## Features

- Flexible input format
- Validation with [goodtables](), [JSON Schema](), [SQL](), or a custom validation class
- Row-by-row feedback on validation results
- Manage and track status of data submissions
- Re-submit previous submissions
- Flexible ultimate destination for data
- [API](docs/api.md) for validation

---

## Requirements

* Python (3.7)
* Django (1.11)
* Goodtables
* pyyaml
* djangorestframework
* psycopg2
* json_logic_qubit
* dj-database-url
* requests

---

## Installation

Install using `pipenv`...

    pipenv install django-data-ingest

Add `'data_ingest'` to your `INSTALLED_APPS` setting.

    INSTALLED_APPS = (
        ...
        'data_ingest',
    )

---

## Examples

Several [examples are provided](./examples/) to demonstrate default and customized
behavior of  `data_ingest`. Follow the [development](#development) instructions to close this repository and install the dependencies required for the examples.

### [default installation](examples/defaults/README.md)

### [p02_budgets](examples/p02_budgets/README.md)

### [p03_budgets](examples/p03_budgets/README.md)

---

## Contributing

See [CONTRIBUTING](CONTRIBUTING.md) for additional information.

---

## Development

To start developing on Django Data Ingest, clone the repository:

    git clone git@github.com:18f/django-data-ingest.git

Install development dependencies:

    pipenv install --dev

### Test Suite

To execute the test suite, install the development dependencies and run:

    python runtests.py

---

## Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
