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
*Caitlin: I think this could be more direct. One or two sentences on what it means to add a product to the database -- think about explaining that this is a fundamental activity involved in managing data with ODC. I think most of the information in this paragraph really falls into the Explanation category from Diataxis, and there's not so much need to dive into it for a Tutorial. I think you want to reassure the user that they're in the right place to learn a key component of working with ODC.*

Adding a product to the ODC index appears straightforward in theory but often proves confusing and challenging in practice. While similarities across products naturally suggest the need for standardization, experience shows that rigid standards rarely endure. Why is this? The utility of data—how it's actually used—ultimately matters more than its structure. Performance considerations vary significantly based on storage technology (cloud versus local disk) and usage patterns (broad spatial coverage versus deep time series analysis). The way information is queried and the volume of data profoundly influence how indexes and metadata should be structured. As a result, while products within the same family share similarities (e.g., Optical Earth Observation data will be more similar than LiDAR) , you'll inevitably encounter variations, particularly when detailed, low-level querying is required.

## Creating *EO3* Product Definitions and indexing a local Product
*Caitlin: I think this is a great statement about what the user can expect to achieve by following the tutorial. The heading above probably isn't so helpful... perhaps just making this part of the introduction? You can have a look at what I wrote for the odc-stac tutorial to get an idea.*

This tutorial will guide you through adding your local *Product* to the ODC index using the *EO3* metadata standard. Following this process ensures your data will be compatible with `datacube-core` and integrate with other applications in the ODC ecosystem, including `datacube-explorer` and `datacube-ows`.

*Caitlin: calling it "the indexing process" isn't overly helpful to a user who doesn't know what indexing is -- perhaps rephrase as "Adding data to your Open Data Cube involves two main steps:"*

The indexing process involves two main steps:
1. Creating *Product Definition* that complies with the *eo3 Product schema*.
2. Preparing *per dataset file metadata* documents that adhere to the *EO3 Dataset schema* that a general refered to as *Dataset Documents*

*Caitlin: I think we could be more specific/direct with these definitions, and rather than including more explanation below, we could try moving those explanations to a different part of the documentation, and just linking to them. You can see an example of how I've defined key concepts (while keeping it brief and direct) in the odc-stac tutorial: https://opendatacube.readthedocs.io/en/latest/tutorials/odc-stac.html#stac-metadata*

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

*Caitlin: Perhaps try and capture some of the critical information from here in the dot points above, and then link to detailed explanation where available. Users probably won't need to directly look at the EO3 repo during the tutorial, but perhaps it could be added as further reading at the end?*

The [*EO3 Product*](https://github.com/opendatacube/eo3/blob/develop/SPECIFICATION-odc-product.md) and [*EO3 Dataset*](https://github.com/opendatacube/eo3/blob/develop/SPECIFICATION.md) metadata types serve as standardized containers for ODC geo-data resource metadata. These specifications, along with utilities for implementing them, are maintained in the  [ODC eo3 repository](https://github.com/opendatacube/eo3/).

The eo3 metadata framework includes several fields that are essential for the proper functioning of the datacube-core library. These critical fields include id (a unique identifier), Product (the product name), crs (coordinate reference system), grid (spatial grid definition), properties (temporal information and other metadata), and measurements (band details including names, units, and file locations).
<!-- Add why these fields are essential -->


# Dataset Documents

*Caitlin: As above, try moving the critical information to the dot point defintions you had earlier. I think those dot points should try and say "this is what product metadata is" and "this is what dataset metadata is".*

### *per dataset metadata*
While the *Product Definition* establishes the structure and access patterns for our *collection* of datasets, it does not specify the location of individual data files or their specific metadata. For this, we need [*EO3 Dataset*](https://github.com/opendatacube/eo3/blob/develop/SPECIFICATION.md) documents. These dataset-specific documents contain crucial information including file locations, storage formats, creation timestamps, the actual coordinate reference system ("crs") used, and the valid data polygon defining the spatial extent. Every data file within your product requires its own corresponding dataset document.

*Caitlin: I don't think you need to say that a different approach will be needed for scaling up. You could perhaps mention this at the end of the tutorial, but mentioning it here might confuse the user and distract them from the goal of the tutorial.*

In this tutorial, we'll implement a Python script that leverages community tools to index a manageable volume of data. For those dealing with larger datasets a more scalable approach is most likely desired.

# The walkthrough - Indexing `io_lulc_annual_v02`

## Understanding the io_lulc_annual_v02 Product and Data

Before creating a  *Product Definition* and *dataset metadta*, you must thoroughly understand two fundamental aspects of your data:
1. What metadata is available for and describes your product?
2. How does the organization and format of your data define both individual datasets and the Product collection as a whole?

The data used in this tutorial originates from the [Impact Observatory 10m Annual Land Use Land Cover (9-class) V2 product collection](https://planetarycomputer.microsoft.com/dataset/io-lulc-annual-v02), available through Microsoft Planetary Computer's STAC catalog. While we're demonstrating local indexing with a downloaded copy in this tutorial, you can find a complementary guide for accessing this data directly via STAC in the ODC GitHub repository.

## Organisation and Format of the Data

The [`LULC Geotiff technical specification`](https://docs.impactobservatory.com/lulc-maps/lulc-maps.html#lulc-geotiff-technical-specifications) thoroughly documents the structure of both the overall **Product** collection and its component datasets. The copy provided in the ODC Google Drive maintains this structure. The key organizational aspects include:

1. The entire **Product** collection is contained within a single folder.
2. Impact Observatory divides there data up into areas they call Supercells. There is 1 dataset file per Supercell with 1 `measurements` per **dataset** available (the Landcover class - `gdalinfo` confirms this).
<!-- TODO: Revise this section to be more clear how the EO3 file relates to each data set file -->

### Accessing Data

The files we are going to use for this tutorial are available in our Google Drive [here.](https://drive.google.com/drive/folders/16wfof-9IHxURAz3BqV7WK-ANNSpv7nvu?usp=sharing) For the `io-lulc-annual-v02` product, we have only a handful of files which cover our area of interest This represents a simpler case, for the instructional purpose of this tutorial, compared to many other products, which may require multiple files arranged in vastly different organizational structures. 

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

# Theory Meets Reality

The example `io-lulc-annual-v02` **Product** used in this tutorial is relatively simple, as is the process of creating the `per dataset metadata` for only 4 spatial tiles. In practice, creating a **Product definition** can require considerable research, including potential direct contact with the people who created it. It is unfortunately common to find that providers do not always make explicit information that is required for use. For example, global open EO data providers may not include information on whether the pixel location is a corner or central point. Sometimes the same provider will do so for one product and not for another, even though they use the same process for both. In other cases, you may find older portions of a collection use a different standard to newer versions (or more confusingly, reprocessed older versions use newer versions and are available in both forms!).

All this means, do your research. *Read* the Product Specification document (or whatever the provider calls it). Look at the data files. Verify your assumptions and their statements with what the actual data looks like - and keep smiling!

## Choices, Choices, Choices

In this walkthrough, a choice was made to create a single **Product** containing all 8 `measurements`. We could just as validly have created 8 separate **Products** or several **Products** with different combinations (e.g., all the `MEASUREMENT*` together). We could also include additional metadata fields about `author`, `algorithm_version` (highly recommend including this), `cloud_cover`, `positional_uncertainty`, `type_of_device`, `device_settings`, and so on. The trick with metadata is not what the provider knows that matters, it's what the user _needs_ or _may want_ to know.

