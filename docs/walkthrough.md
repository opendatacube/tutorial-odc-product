# The ODC Metadata Model and Indexing Process

## Table of Contents

- [The ODC Metadata Model and Indexing Process](#the-odc-metadata-model-and-indexing-process)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Creating *eo3* Product Definitions and indexing a local Product](#creating-eo3-product-definitions-and-indexing-a-local-product)
    - [The *eo3* metadata specifications](#the-eo3-metadata-specifications)
    - [*Product Definition* - making expectations **Product** specific](#product-definition---making-expectations-product-specific)
    - [*per dataset metadata*](#per-dataset-metadata)
    - [ODC database management - Indexing, Deleting, Updating](#odc-database-management---indexing-deleting-updating)
  - [The walkthrough - Indexing `io_lulc_annual_v02`](#the-walkthrough---indexing-io_lulc_annual_v02)
    - [Tutorial environment](#tutorial-environment)
    - [One time setup](#one-time-setup)
    - [Configure VS Code environment](#configure-vs-code-environment)
    - [Understanding the io_lulc_annual_v02 Product and Data](#understanding-the-io_lulc_annual_v02-product-and-data)
    - [Creating a *Product Definition*](#creating-a-product-definition)
    - [Preparing *per dataset metadata*](#preparing-per-dataset-metadata)
    - [Processing All the Data Files](#processing-all-the-data-files)
    - [Indexing the Product](#indexing-the-product)
    - [Verify the product is correct with `datacube.load()`](#verify-the-product-is-correct-with-datacubeload)
    - [When it all goes wrong - Removing the Product from the Index](#when-it-all-goes-wrong---removing-the-product-from-the-index)
  - [Administration for new products in Production](#administration-for-new-products-in-production)
    - [Updating the Database Ancillary Tables](#updating-the-database-ancillary-tables)
  - [Theory Meets Reality](#theory-meets-reality)
  - [Choices, Choices, Choices](#choices-choices-choices)
  - [Common Errors](#common-errors)

# Introduction
Adding a product to the ODC index appears straightforward in theory but often proves confusing and challenging in practice. While similarities across products naturally suggest the need for standardization, experience shows that rigid standards rarely endure. Why is this? The utility of data—how it's actually used—ultimately matters more than its structure. Performance considerations vary significantly based on storage technology (cloud versus local disk) and usage patterns (broad spatial coverage versus deep time series analysis). The way information is queried and the volume of data profoundly influence how indexes and metadata should be structured. As a result, while products within the same family share similarities (e.g., Optical Earth Observation data will be more similar than LiDAR) , you'll inevitably encounter variations, particularly when detailed, low-level querying is required.

## Creating *EO3* Product Definitions and indexing a local Product

This tutorial will guide you through adding your local *Product* to the ODC index using the *EO3* metadata standard. Following this process ensures your data will be compatible with `datacube-core` and integrate with other applications in the ODC ecosystem, including `datacube-explorer` and `datacube-ows`.

The indexing process involves two main steps:
1. Creating *Product Definition* that complies with the *eo3 Product schema*.
2. Preparing *per dataset file metadata* documents that adhere to the *EO3 Dataset schema* that a general refered to as *Dataset Documents*

To understand the process, it's important to recognize three key components:
1. *EO3* Product and Datasets schemas - These are standardized specifications defined by ODC.
2. *Product Definition* - This is specific to your product in your data cube and its intended use cases.
3. *Per dataset metadata* - This contains unique information describing each individual dataset within your product.

The complete product addition workflow consists of:
1. **Developing** a comprehensive *Product Definition*
2. **Preparing** detailed *per dataset metadata*
3. **Indexing** the dataset metadata into the ODC database.
<!-- 4. **Update ancillary tables** in the ODC database for `datacube-explorer` and `datacube-ows`. -->

### The *EO3* metadata specifications

The [*EO3 Product*](https://github.com/opendatacube/eo3/blob/develop/SPECIFICATION-odc-product.md) and [*EO3 Dataset*](https://github.com/opendatacube/eo3/blob/develop/SPECIFICATION.md) metadata types serve as standardized containers for ODC geo-data resource metadata. These specifications, along with utilities for implementing them, are maintained in the  [ODC eo3 repository](https://github.com/opendatacube/eo3/).

The eo3 metadata framework includes several fields that are essential for the proper functioning of the datacube-core library. These critical fields include id (a unique identifier), Product (the product name), crs (coordinate reference system), grid (spatial grid definition), properties (temporal information and other metadata), and measurements (band details including names, units, and file locations).
<!-- Add why these fields are essential -->


# Dataset Documents

### *per dataset metadata*
While the *Product Definition* establishes the structure and access patterns for our *collection* of datasets, it does not specify the location of individual data files or their specific metadata. For this, we need [*EO3 Dataset*](https://github.com/opendatacube/eo3/blob/develop/SPECIFICATION.md) documents. These dataset-specific documents contain crucial information including file locations, storage formats, creation timestamps, the actual coordinate reference system ("crs") used, and the valid data polygon defining the spatial extent. Every data file within your product requires its own corresponding dataset document.

In this tutorial, we'll implement a Python script that leverages community tools to index a manageable volume of data. For those dealing with larger datasets a more scalable approach is most likely desired.

# The walkthrough - Indexing `io_lulc_annual_v02`

## Understanding the io_lulc_annual_v02 Product and Data

To create a *Product Definition* and *dataset metadta*, you need to understand two key aspects of your data:
1. What metadata is available for the product?
2. How the organization and format of the data form an individual **dataset** and the **Product** collection as a whole.

This data is originally from a STAC indexed data source freely available on the [Microsoft Planetary Computer and is from the Impact Observatory 10m Annual Land Use Land Cover (9-class) V2 product collection](https://planetarycomputer.microsoft.com/dataset/io-lulc-annual-v02). It is used as an example for local indexing with this copy and there is a matching tutorial for using it directly with ODC via STAC on the ODC github.

## Organisation and Format of the Data

The [`LULC Geotiff technical specification`](https://docs.impactobservatory.com/lulc-maps/lulc-maps.html#lulc-geotiff-technical-specifications) provides details on the structure of the **Product** collection and the individual datasets. The ODC Google Drive is of the same form. Here are three key points:

1. The **Product** collection is contained within a single folder.
2. There is 1 file per dataset Supercell with 1 `measurements` per **dataset** available (the Landcover class - `gdalinfo` confirms this).

### Accessing Data

To access an entire **dataset** tile for the `io-lulc-annual-v02` product, you need to collect one file only.

For other products there can be many files and they may be groups entirely differently. This one is particularly simple.

### Data Organisation Choices by the Provider

The provider has chosen to group all individual **dataset** files together. Another common approach is to have a single folder containing all measurements for a single **dataset** (as seen with Landsat data). Or by region code, or by date, or by measurements.

_Tip:_ Much of metadata and data organisation is based on personal preference rather than strict requirements, and that's perfectly fine (unless its for a standard, then there is war! Less tongue in cheek, the goal of a standard is to make life easier for downstream users. Changing the file organisation can be a massive job for the provider, so there are underlying reasons for resistance to such change.)

## Preparing *per dataset metadata*

Up to this point, we have identified important values for the **Product** as a whole (e.g., product name `io_lulc_annual_v02`) and described what a dataset should contain (e.g., number and name of the `measurements`). What remains is to create a dataset metadata record for every dataset to populate the required fields from the [ODC eo3 dataset specification](https://github.com/opendatacube/eo3/blob/develop/SPECIFICATION.md). These fields include `measurements.path` (pointing to the location of the data file for that measurement), dataset `geometry` (with the valid data polygon), and dataset `grids` (with information on the `odc_geo.GeoBox` for the entire dataset). Each of these values is dataset-specific and is copied or derived from the source data. For example, the `geometry` valid data polygon may be supplied by the source (as it is in STAC records) or computed by analyzing all of the measurements' valid pixels and constructing a valid data polygon for _all_ measurements.

Per dataset metadata preparation is therefore the most complex component of indexing data, and it is necessarily bespoke to the source dataset. There are some commonalities and thus some common libraries in the ODC and EASI communities. In this tutorial, we'll be using the `easi_assemble.py` function, which is derived from the ODC equivalent. Alongside this, there is an `easi_prepare_template.py` file containing a template script for using the `easi_assemble.py`. The script and process are fairly straightforward and follow these steps for each dataset:

1. **Create an `EasiPrepare` object**: Initialize it with the `dataset_path`, `product_yaml` (the *Product Definition*), and `output_path` for the metadata file. This will initialize an **ODC dataset document** with placeholders for all the required values (and any optional ones) described in the *Product Definition*. Here's a snippet from the code showing what is created at the top level:
  ```python
  self._dataset = DatasetDoc()  # https://github.com/opendatacube/eo-datasets/blob/develop/eodatasets3/model.py
    # id            UUID                        Dataset UUID
    # label         str                         Human-readable identifier for the dataset
    # product       ProductDoc                  The product name
    # locations     List[str]                   Location(s) where this dataset is stored
    # crs           str                         CRS string for the dataset (measurement grids), "epsg:*" or WKT
    # geometry      BaseGeometry                Shapely geometry of the valid data coverage
    # grids         Dict[str, GridDoc]          Grid specifications for measurements
    # properties    Eo3Dict                     Raw properties
    # measurements  Dict[str, MeasurementDoc]   Loadable measurements of the dataset
    # accessories   Dict[str, AccessoryDoc]     References to accessory files
    # lineage       Dict[str, List[UUID]]       Links to source dataset uuids
  ```

2. **Populate the `DatasetDoc` with values**: Copy or derive values from the source data using the mapping identified earlier. This usually requires parsing source metadata files, filenames, paths, and information contained in data files like the GeoTIFFs. Populating `measurements` from GeoTIFFs and computing `geometry` and `grids` is a common requirement. The `EasiPrepare` and ODC equivalent include helper functions that can obtain and derive these values from the GeoTIFF files directly, given a list of files.

3. **Write the `Dataset document` to a file**: This prepares the metadata file for future indexing.

The dataset document is written to a file and not indexed directly to the ODC database. This pattern is commonly used in the ODC community as it allows reindexing of **Products** without reanalysis and extraction of metadata if the database requires a rebuild. For a very large collections, this can be important as the reprocessing cost may be significant, and the additional storage of a small text document is usually negligible in cost.

The file [`tasks/prepare_io_lulc_annual_v02_metadata.py`](../tasks/prepare_io_lulc_annual_v02_metadata.py) contains a complete example with detailed comments for the `io_lulc_annual_v02` *Product Definition*. The `tests` folder contains [a matching `pytest`](../tests/test_prepare_io_lulc_annual_v02_metadata.py) which will process a single dataset from the `io_lulc_annual_v02` data for testing.

### Processing All the Data Files

Now that we can process a single dataset, processing the entire collection involves repeating the process. The method for looping over datasets depends on the number of datasets and the amount of analysis being performed. Here are three common methods used by the EASI community:

1. **Simple Python Loop** (with or without parallelization): For small collections like this tutorial, this is the simplest method. It can be straightforward if a complete dataset is held in a single folder structure or more involved if a dataset is spread across folders and mixed with other datasets (as in this tutorial).
2. **During Product Creation**: Often the best and simplest implementation, as all required metadata is at hand.
3. **Argo Workflow**: For large collections and significant analysis, an Argo Workflow is a highly scalable approach (e.g., running an atmospheric correction workflow on a multi-decadal continental Landsat collection).

For this tutorial, we'll use a simple Python script to wrap the [`prepare_io_lulc_annual_v02_metadata.py`](../tasks/prepare_io_lulc_annual_v02_metadata.py) function. Since the datasets are intermingled and spread across the folder structure, we can use the tile coordinates and abbreviated measurement prefixes in the filenames to identify measurements and the number of datasets. The workflow script for this can be found in [`workflows/io_lulc_annual_v02_product_metadata_generator.py`](../workflows/io_lulc_annual_v02_product_metadata_generator.py).

## Indexing the Product

Indexing a product into the ODC database requires two steps:
1. Add or update the **product definition** in the ODC database.
2. Add one or more **dataset metadata** files.

### Adding the Product Definition to the ODC Database

Once you have the **product definition** file, adding it is straightforward but requires ODC database administration privileges (not PostgreSQL server administrative privileges). Details are in the ODC documentation section on [indexing data](https://datacube-core.readthedocs.io/en/latest/installation/indexing-data/step-guide.html#loading-product-definitions). For our tutorial you have the administration privileges for the local ODC postgres database and can add the product definition:

```bash
$ datacube product add ./products/impact_observatory/io_lulc_annual_v02.yaml
```

If you made a mistake or otherwise change your product definition, you can update it with:

```bash
$ datacube product update ./products/impact_observatory/io_lulc_annual_v02.yaml
```

If you receive an `unsafe update` error message, it indicates that the definition might be changing in a way that is inconsistent with the previous definition and may break things. Use the command line argument to update and indicate the changes are safe to proceed if your changes are intentional.

### Adding Dataset Metadata Files

With the product definition loaded, the next step is to add the **dataset metadata** files to the index. There are three different ways to index:

1. One at a time using `datacube dataset add <path-to-dataset-document-yaml>`.
2. Using a utility like `s3-to-dc` to scan through an S3 bucket and index the entire collection under that prefix.
3. Programmatically via the ODC datacube-core API.

The primary difference between these approaches is performance at scale and ease of use. Indexing is a transactional database operation, and doing them in batches is considerably faster than one at a time. `datacube dataset add` and `s3-to-dc` both add one at a time, but `s3-to-dc` uses parallel operations, making it slightly faster. The `easi-workflows` are beginning to replace `s3-to-dc` with new programmatic variants that include batch transactions and parallelization, making them several orders of magnitude faster.

There is a short bash script that will run `datacube dataset add` on all the data files [here](../workflows/add_io-lulc-annual-v02_datasets_to_odc_db.sh). You can run it with;

``` bash
  $ ./workflows/add_io-lulc-annual-v02_datasets_to_odc_db.sh
```

## Verify the product is correct with `datacube.load()`

After indexing, the `datacube-core API` should operate fully, e.g., `datacube.load(...)`.

You can test the new product using the [`notebooks/io_lulc_annual_v02.ipynb`](../notebooks/io_lulc_annual_v02.ipynb). You will need to select the `localdb` kernel for the notebook created during tutorial setup so your `datacube` code will use the local database. _Use the Jupyter environment for this_ - it has better interactive visualisation support.

## When it all goes wrong - Removing the Product from the Index

The ODC doesn't have a product deletion tool (shock horror!). Members of the ODC community have contributed scripts to manually delete an entire ODC Product and related records in ODC, Explorer, and OWS DB. The SQL scripts need to be applied in a specific order (see the [`README.md`](../tools/odc-product-delete/README.md)) and require ODC database administration privileges in the `.datacube-conf` for all tables to be removed. The EASI [`tools/delete_product.py`](../tools/delete_product.py) CLI utility simplifies this process. If all permissions are in place, running the script with the name of the product will remove it after confirmation.

You may see a few errors in the SQL if the OWS and Explorer tables haven't been initialized yet. This can occur during initial product creation if you start indexing a product and discover a mistake and need to start over before running the `cubedash-gen` and `datacube-ows-update` commands. Those errors can safely be ignored under those conditions.

For the tutorial you can of course just delete the entire local database using the command described earlier.

# Administration for new products in Production

Once your product is ready to go you will need to work with your EASI Administrator to move to production. In addition to the steps above for metadata creation and indexing your Administrator will need to address some additional actions.

## Updating the Database Ancillary Tables

ODC deployments commonly use both the `datacube-explorer` application and `datacube-ows`. These use two additional database schemas added to the ODC core tables. When a new product or dataset is added, it is necessary to update these schemas using the associated commands from the respective application. You will need administrative privileges against the respective schemas and a running Pod containing the application libraries and cli.

For `datacube-explorer` with a running Pod containing the `explorer` application:

```bash
$ cubedash-gen --no-init-database --refresh-stats <product name>
```

For `datacube-ows` with a running Pod containing the `ows` application:

```bash
$ datacube-ows-update --views
$ datacube-ows-update <product name>
```

Several additional options exist to control how updates are performed (e.g., complete refresh, refresh since last update only, refresh `--all` products).

In production these additional processes are normally automated.


# Theory Meets Reality

The example `io-lulc-annual-v02` **Product** used in this tutorial is relatively simple, as is the process of creating the `per dataset metadata` for only 4 spatial tiles. In practice, creating a **Product definition** can require considerable research, including potential direct contact with the people who created it. It is unfortunately common to find that providers do not always make explicit information that is required for use. For example, global open EO data providers may not include information on whether the pixel location is a corner or central point. Sometimes the same provider will do so for one product and not for another, even though they use the same process for both. In other cases, you may find older portions of a collection use a different standard to newer versions (or more confusingly, reprocessed older versions use newer versions and are available in both forms!).

All this means, do your research. *Read* the Product Specification document (or whatever the provider calls it). Look at the data files. Verify your assumptions and their statements with what the actual data looks like - and keep smiling!

## Choices, Choices, Choices

In this walkthrough, a choice was made to create a single **Product** containing all 8 `measurements`. We could just as validly have created 8 separate **Products** or several **Products** with different combinations (e.g., all the `MEASUREMENT*` together). We could also include additional metadata fields about `author`, `algorithm_version` (highly recommend including this), `cloud_cover`, `positional_uncertainty`, `type_of_device`, `device_settings`, and so on. The trick with metadata is not what the provider knows that matters, it's what the user _needs_ or _may want_ to know.

Some tips on choices:
- If the data is created by you, it pays to have a _Product Governance document_ in place both for change control and for joint discussion with users to discover what is required that was missed. Keep the version in sync with the `product name` and **Product definition** in your source code repository - if you can, add the document to the source code as well!
- If in doubt, add the metadata. Generally speaking, adding a field of metadata isn't too onerous and you are unlikely to be chided for having included something that you later discover isn't useful.
- When using someone else's data (e.g., Landsat), you will often want to copy the source metadata into your derived product (e.g., the Sun angle is still the sun angle!). This is often more convenient for users than having to play match-up to the original data (which may have been reprocessed upstream and no longer identical anyway!).
- Definitely borrow good ideas from other people's **Product definitions**. The Space Agencies have been doing this a long time and do have well-developed standards and governance practices (e.g., [CEOS WGISS Best Practice Guides](https://ceos.org/ourwork/workinggroups/wgiss/documents/)). Similarly, the [STAC](https://stacspec.org/en) community has gathered momentum and created some base conformance models (much of which has expanded from the original simple STAC model to include the CEOS best practices). None are perfect. Some are complex. It depends on the use-cases they are developed to support.

Ultimately, the choice is yours.

**Tip:** Did you know the **product definitions** and **dataset documents** are available from any `odc-explorer` interface. Here's an example for [Digital Earth Australia Landsat 9c ard 3](https://explorer.dea.ga.gov.au/products/ga_ls9c_ard_3). At the bottom of that page is the **product definition** pretty printed (Click the [raw](https://explorer.dea.ga.gov.au/products/ga_ls9c_ard_3.odc-product.yaml) link to get the `YAML` version). You can also get to the dataset documents from that page.

## Common Errors

There are some common errors in **Product definition** creation to watch out for:
1. Not including a collection version in the `product name` - you will update your product collection at some point and the name must be unique. Commonly a collection number is added to the name e.g., io_lulc_annual_v02_**c3**.
2. Not creating a unique `UUID` for the product or `dataset_id` for datasets. The `easi_prepare_template.py` includes this code:

    ``` python
    # Static namespace (seed) to generate uuids for datacube indexing
    # Get a new seed value for a new driver from uuid4()
    UUID_NAMESPACE = None  # FILL. Get from the product family or generate a new one with uuid.UUID(seed)
    ```

    The `UUID` namespace (seed) needs to be **unique** in the ODC database or the dataset records will be considered part of the same product. The same is true for the `dataset_id`. It doesn't matter what it is, only that it is unique. The most common mistake here is to _copy and paste_ code from a similar product and forget to ensure these are unique for the new product. The side effects can be very difficult to detect at runtime.

3. Valid data polygon creation: When creating the valid data polygon for a dataset, it needs to be done across _all_ measurements (one valid polygon showing valid data for all measurements). There are many ways to do this: bounding box, convex hull, multi-polygon. The objective isn't perfection, but as an aid to ODC query filters to eliminate entire datasets that are not part of the output. The `easi_assemble.py` code includes several options for this calculation right down to vectorizing full valid pixel masks with multi-polygons. Given the spatial analysis required to do this, different algorithms may fail on sparse (e.g., patchy cloud) datasets. Choose the best option that works stably for your product; if that is a basic bounding box, it will still serve its purpose.
