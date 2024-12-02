# EASI EO3 metadata preparation

EASI uses the `eodatasets3 library` from (GA/)ODC, [https://github.com/opendatacube/eo-datasets](https://github.com/opendatacube/eo-datasets), to help produce `eo3` dataset description documents.

The `eodatasets3` library includes a number of features and capabilities relevant to GA's workflows.

For EASI, we choose to adapt the same "assembler" entry point but simplify it for EASI's workflows.

## Current

`easi_prepare_template.py`: A template "dataset prepare" script that can be adapted for a specific product

- Description of required and optional metadata fields
- There are no "naming conventions" but rather suggestions for how the fields can be populated
- Patterns that have proven useful as shown but can be discarded if they don't suit your product

`easi_assemble.py`: EASI's "assembler" class, adapted from `eodatasets3/assemble.py`

- Remove "naming conventions"
- Simplify input path handling
- Simplify to include only the necessary steps to improve readability and traceability
- Optional S3 sources (includes features from `eo3_s3_assemble.py`)
- Relies on Product yaml to ensure necessary fields are linked correctly (`metadata:product_name`, `measurements`)
- Updated from `eo3_assemble.py` to reflect `eodatasets3` refactor in Q4 2021, and our past experience

