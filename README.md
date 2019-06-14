# ReVAL

ReVAL (Reusable Validation & Aggregation Library) is a Django App for validating and aggregating data via API and web interface.

For the web interface, it can manage data submitted as file uploads to a central gathering point, and it can perform data validation, basic change tracking and duplicate file handling.  Each file generally contains multiple data rows, and each user may submit multiple files.

For the API, it can perform data validation, and view uploads that were done via the web interface.

---

## Features

- Flexible input format
- Validation with:
  - [goodtables](https://github.com/frictionlessdata/goodtables-py)
  - [JSON Logic](https://github.com/QubitProducts/json-logic-py)
  - [SQL](https://sqlite.org/lang_keywords.html)
  - [JSON Schema](https://github.com/Julian/jsonschema)
  - a custom validation class
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
* djangorestframework
* psycopg2
* json_logic_qubit
* dj-database-url
* requests

---

## Quick Installation

If you would like to use ReVAL in your Django project, install using `pipenv` in your project...

- Replace `<version>` with the latest tag i.e. `v0.2` or
- Replace with `master` if you would like to work with the latest development version

```bash
pipenv install -e git+https://github.com/18F/ReVAL.git@<version>#egg=data-ingest
```

Add `'rest_framework'`, and `'data_ingest'` to your `INSTALLED_APPS` setting.

```python
INSTALLED_APPS = (
    ...
    'rest_framework',
    'data_ingest',
)
```

Please see [default installation](./examples/defaults/) for more setup instructions.

---

## Examples

Several [examples are provided](./examples/) to demonstrate default and customized behavior of  `data_ingest`.
Follow the [development](#development) instructions to close this repository and install the dependencies required for the examples.

### [default installation](examples/defaults/README.md)

### [p02_budgets](examples/p02_budgets/README.md)

### [p03_budgets](examples/p03_budgets/README.md)

---

## API

To perform data validation with API, see [API documentation](docs/api.md).

---

## Deployment on Cloud.gov

All of the examples provided will show you how to run them locally.  If you are interested in using [cloud.gov](https://cloud.gov) as your platform, here's a [basic installation guide on cloud.gov deployment](docs/cloud.gov.md).


## Contributing

See [CONTRIBUTING](CONTRIBUTING.md) for additional information.

---

## Development

To start developing on Django Data Ingest, clone the repository:

```bash
git clone git@github.com:18f/ReVAL.git
```

Install development dependencies:

```bash
pipenv install --dev
```

If you run into any issues installing packages in the `Pipfile`, you can try to install the particular package individually again.

### Test Suite

To execute the test suite, install the development dependencies and run:
```bash
python runtests.py
```

---

## Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
