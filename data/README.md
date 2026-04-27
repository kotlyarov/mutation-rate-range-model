# Data Directory

This directory is for empirical data used by the Mutation Rate Range Model.

## Current status

No curated project data is included yet.

The first implementation should work without data files.

## Directory structure

```text
data/
  raw/
  processed/
  external/
  README.md
```

## `raw/`

Original downloaded data files.

Do not manually edit these files.

## `processed/`

Generated cleaned data files.

Every file in this directory should be reproducible from scripts or notebooks.

## `external/`

Small reference files or metadata tables.

## Required metadata

For every dataset, document:

```text
source_name
source_url
access_date
license_or_terms
download_method
raw_filename
processing_script
notes
```

## Rule

Do not present exploratory model defaults as fitted values unless the fitting process and data sources are documented.
