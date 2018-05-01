# django-data-ingest

`data_ingest` is a reusable Django project managing data submisstions to a central
gathering point by file uploads.  Each file generally contains multiple data rows, and
each user may submit multiple files.

The [default installation](docs/default.md) exposes a very basic and minimal
workflow, which can be [customized](docs/customize.md) for your needs.

## Features

- Flexible input format
- Validation with [goodtables](), [JSON Schema](), or a custom validation class
- Row-by-row feedback on validation results
- Manage and track status of data submissions
- Re-submit previous submissions
- Flexible ultimate destination for data

## Contributing

See [CONTRIBUTING](CONTRIBUTING.md) for additional information.

## Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
