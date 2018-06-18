# 10x Data Federation Project (Federated Data Ingest Tool)

The Federated Data Ingest (also known as `data_ingest`) is a reusable Django project managing data submitted as file uploads
to a centralgathering point.  Each file generally contains multiple data rows, and
each user may submit multiple files.

## Background

There is significant demand in government (from federal to state / local) for tools that make the process of aggregating data from multiple parties and sources easier.  Long term, successful federated data efforts are unlikely if the process by which data are collected, aggregated and validated cannot be improved.  Gathering these data in a timely fashion by using tools that are complementary to existing workflows (e.g. they do not add additional time and effort on the data provider) and that are easy to use will help modernize the way the federal government functions and interacts with other government agencies.

For more information about this project and scope, read the [U.S. Data Federation report](https://github.com/18F/data-federation-report/blob/master/DataFederationFramework.md) from Phase I. 


---

## Features

- Flexible input format.  The tool allows for submissions via form upload, or through an on-demand API to validate records in real-time.
    - a. CSV, TSV, JSON, etc.
    - Submitted file staged for review of validation failures 
    - Submitted file/data delivered upon review

- Validation with [goodtables](), [JSON Schema](), [SQL](), or a custom validation class
- Row-by-row feedback on validation results
- Manage and track status of data submissions
- Re-submit previous submissions
- Flexible ultimate destination for data
- [API](docs/api.md) for validation

---

## Requirements

* Python (3.5, 3.6)
* Django (1.11)
* Goodtables
* pyyaml
* django-rest-framework
* psycopg2
* json-logic-py (https://github.com/qubitdigital/json-logic-py)

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
