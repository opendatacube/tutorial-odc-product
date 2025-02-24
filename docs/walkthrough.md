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

Adding a product to the ODC index is theoretically simple but practically confusing, challenging, and frustrating. The similarities across products result in a call for a standard data structure, but creating Yet Another Standard often fails. Why? Decades of standards development have shown that they do not and cannot last. The data's *use* is more important than its structure and content. File formats impact performance based on storage technology (e.g., Cloud vs local disk) and usage patterns (e.g., spatial area vs deep time series). How information is queried and the data volume significantly affect how indexes and metadata content are determined. Therefore, whilst you will find similarities between products, especially of the same family (e.g., Optical Earth Observation data will be more similar than LiDAR), there will inevitably be minor differences, and even more if you require a low level details to be queried.

_Why do people continue to develop standards then?_

While standards do not *solve* all problems, they help keep issues *manageable within a given context*.

The Open Data Cube (ODC) has both a context and an opinion about data _use_, which has driven its development and the way it handles data, and the metadata used in indexing it:

1. **Context:** The primary use-case is Earth Observation (EO) data analysis, specifically geospatial grids of time series data. Such data can be "produced and/or downloaded and managed locally" or "used directly in the Cloud from the Provider."
2. **Opinion:** The **required** metadata for indexing and query support is the minimum needed to support the ODC `datacube.load()` and related functions (e.g., space, time, measurements) in a performant manner. **Optional** additional metadata fields can be queried but may not be performant.

Given the constant development of new approaches and variations, ODC documentation and code support several different ways of doing things. The goal is to keep this manageable. At the time of writing, ODC v1.8 is current, and the development roadmap from 1.8 to 1.9 (release candidate) and 2.0 indicates the various metadata formats being deprecated and new ones supported. The two metadata formats currently maintained are:

1. *eo3* for locally managed products in the ODC database.
2. `STAC` (Spatio Temporal Asset Catalogues), the de facto standard to Cloud-based EO data distribution, used by EO data providers both commercially and by members of the Committee on Earth Observation Satellites (e.g., NASA, ESA).

*eo3* and `STAC` have an interconnected history, which we won't delve into in this tutorial. The ODC is steadily integrating native support for direct STAC usage by `datacube.load()`, as seen in the `odc-stac` library, which will be integrated into ODC 2.0 (possibly even 1.9). Applications like `odc-explorer` will also publish STAC from the datacube database (i.e., converting from *eo3* on the fly). So these are similar but not quite the same (yet).

## Creating *eo3* Product Definitions and indexing a local Product

This tutorial focuses on how to add your local *Product* to the ODC index using *eo3* metadata so it can be used with `datacube-core` and other applications in the ODC ecosystem (e.g., `datacube-explorer` and `datacube-ows`).

The process is straightforward:
1. Create an *eo3 Product schema* compliant *Product Definition*.
2. Prepare *per dataset metadata* documents compliant *eo3 Dataset schema*.

There are three key components:
1. *eo3* Product and Datasets schemas - defined by ODC.
2. *Product Definition* - unique to your product and use.
3. *per dataset metadata* - unique information about each dataset in your product.

Managing a product requires:
1. **Developing** a *Product Definition*
2. **Preparing** *per dataset metadata*
3. **Index** the dataset metadata into the ODC database.
4. **Update ancillary tables** in the ODC database for `datacube-explorer` and `datacube-ows`.

### The *eo3* metadata specifications

The [*eo3 Product*](https://github.com/opendatacube/eo3/blob/develop/SPECIFICATION-odc-product.md) and [*eo3 Dataset*](https://github.com/opendatacube/eo3/blob/develop/SPECIFICATION.md) metadata types "contains the metadata for an ODC geo-data resource." The full specifications and utilities for working with them can be found in the [ODC eo3 repository](https://github.com/opendatacube/eo3/).

This metadata type includes fields that are essential for the `datacube-core` library to function. Applications and libraries in the ODC ecosystem require this information and will only _depend_ on this information, though it is possible to add custom metadata that will work with ODC queries (e.g., to enable filtering by custom fields).

This tutorial focuses on the required *eo3* data fields including `id`, **Product**, `crs`, `grid`, `properties` (e.g., time), and `measurements` (e.g., band name, units, file location). Where possible, the content will be restricted to fields not identified as deprecated in the ODC 1.9 release candidate. Since ODC 1.8 is the production version at the time of writing, a few legacy fields will still be required.

The *eo3* specification is predefined by the ODC but allows a great deal of flexibility (e.g., the `properties` field can define arbitrary user-specified metadata). This tutorial doesn't delve into those details but illustrates a minimum viable example of a **Product** and `dataset metadata` compliant with the specification and thus supported by the ODC ecosystem.

### *Product Definition* - making expectations **Product** specific

The *eo3* specifications outline the general properties required for ODC to function. A *Product Definition* makes this specific to a particular product. For example, instead of just `measurements`, a *Product Definition* will specify that _"this product will contain 2 measurements named *blue* and *red*, and both will be of data type `uint16`."_

A *Product Definition* has a minimum required content as shown in the [eo3 ODC product specification](https://github.com/opendatacube/eo3/blob/develop/SPECIFICATION-odc-product.md). The hands-on walkthrough below will illustrate this with an example.

### *per dataset metadata*

Whilst the *Product Definition* outlines what our *collection* of datasets should contain. The final  [*eo3 Dataset*](https://github.com/opendatacube/eo3/blob/develop/SPECIFICATION.md) documents required are *specific to each dataset* and include details such as where to find the data, the storage format, the creation datetime of the dataset, the actual stored `crs`, and the valid data polygon. Each dataset needs its own document, potentially for millions of datasets!

Creating metadata for each dataset is best done automatically. Much of this metadata can be derived from the dataset itself, as it is often a copy or summary of the actual data. In the ODC community, this process is commonly referred to as the **prepare** stage. It can be as simple as a Python script, optionally using some ODC community tools built for this purpose, or as complex as a fully automated Argo Workflow. The latter gathers incoming source data, performs analysis to create a derived custom product, and prepares the resulting dataset metadata, even automating the indexing and updating of other ODC components, and does so by orchestrating potentially 1000's of compute cores in parallel. That's quite a lot!

For this tutorial, we will use a Python script with some community tools and index a modest amount of data. Examples of more complex and highly scalable approaches can be found in the `easi-workflows` repository available to EASI Enterprise partners.

###  ODC database management - Indexing, Deleting, Updating

There are several ODC tools available for managing the ODC database once you have the metadata in place. The landscape can be somewhat chaotic due to the unique operational requirements of different ODC deployments. The scale of a collection also significantly impacts the tools and techniques used. For example, adding a single dataset via the CLI is feasible, but doing so for 1,000,000 datasets is impractically slow, even with automation, due to the lack of transaction batching. The techniques used in this tutorial are those currently employed by the EASI community. While these methods are effective, there is still room for improvement in tooling. Details will be illustrated by example in the walkthrough.

# The walkthrough - Indexing `io_lulc_annual_v02`

## Tutorial environment

There are many, often arbitrary, choices to be made in creating a metadata for a **Product**. The development process will be interative and require verification by using the data with `datacube.load()` and other ODC API calls. Doing this with the production ODC database is clearly unwise and having `test` code is highly recommended. To support this for ordinary users the tutorial environment supports two ways to working:

  1. Visual Studio Code and Docker based Dev Container (Local option): The `.devcontainer` and `docker` folders (and anciallary files) will use `docker-compose` to spin up two containers - one which VS Code will attach to with a python environment including the ODC; the other with a postgresql server with an empty but initialised datacube schema.
  2. Jupyter Labs ODC deployment (e.g. CSIRO EASI or DEA Sandbox): Typically a Jupyter Labs ODC deployment does not allow users to configure a system level postgres server nor support per user development databases. This tutorial includes instructions that support installing a local postgres server in the users home directory which can be used for ODC product development and testing. This does not require any administrative privileges nor does it impact any other users. With in the Jupyter Labs environment if you also have access to VS Code (e.g. in CSIRO EASI you can open VS code in the browser) we *highly recommend the use of the VS Code interface rather than Jupyter for the metadata scripts and testing*. Debugging and testing scripts for indexing is simpler with a full IDE as you have better debugging tools for stepping through code and checking variable assignments. Verifying indexing is correct will use the Jupyter Notebook environment since it has better support for visualisation.

### One time setup

1. Git clone the tutorial repository:

  ``` bash
  $ git clone https://<LOCATION>/odc-product-tutorial
  ```
2. Download sample data
    In this tutorial, we'll use the io-lulc-annual-v02 data available in the [ODC Sample Data Folder](https://drive.google.com/drive/folders/16wfof-9IHxURAz3BqV7WK-ANNSpv7nvu?usp=drive_link) folder.

    **Follow the link and download the files and place them in the `data` folder:**
    ```
    15M-2017.tif
    15N-2017.tif
    16M-2017.tif
    16N-2017.tif
    ```

#### If running in a Jupyter ODC environment:
  1. Install and run a personal ODC Postgres database - [instructions](../tutorial-env/personal-odc-db/README.md)

  2. Create a custom jupyter kernel that points at the personal ODC database:

  ``` bash
  $ /env/bin/python -m ipykernel install --user --name localdb --env DATACUBE_DB_URL "postgresql:///datacube?host=/tmp"
  ```

##### Managing the Tutorial Environment Personal ODC Database

After completing the one-time setup, you will have started a PostgreSQL and initialized it with an ODC database without any `Products`.

Using the personal database requires manually starting and stopping it. The `db.sh` utility script simplifies this process. Running it will display the available options:

```bash
$ ./tutorial-env/personal-odc-db/db.sh
Invalid parameter. Please use one of 'start, stop, status, init, log, env, fetch, snapshot, delete'.
```

For this tutorial, you will primarily use the `env`, `start`, `stop`, `delete`, and `status` options.

- **`env`**: Sets up the environment variables to point to the local database. Use `eval` to apply these variables to the **local** terminal:
  ```bash
  eval "$(./tutorial-env/personal-odc-db/db.sh env)"
  ```
  To see the variables being set, run:
  ```bash
  ./tutorial-env/personal-odc-db/db.sh env
  ```

- **`start`**: Starts the database.
  ```bash
  ./tutorial-env/personal-odc-db/db.sh start
  ```

- **`stop`**: Stops the database. It is important to stop the database to avoid corruption errors. If you forget most of time you can just start it again. Sometimes it will be start over again! (i.e., `delete` the database)
  ```bash
  ./tutorial-env/personal-odc-db/db.sh stop
  ```

- **`status`**: Check if the database is running.
  ```bash
  ./tutorial-env/personal-odc-db/db.sh status
  ```

- **`delete`**: Completely removes the database and starts over.
  ```bash
  ./tutorial-env/personal-odc-db/db.sh delete
  ```

### Configure VS Code environment

1. In VS Code Set the Python interpreter to use the Python Virtual Environment - `/env/bin/python`
1. Configure the `.vscode/launch.json` with:
  ``` json
  {
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
      {
        "name": "Python Debugger: Current File",
        "type": "debugpy",
        "request": "launch",
        "program": "${file}",
        "console": "integratedTerminal",
        "justMyCode": true,
        "env": {
          "PYTHONPATH": "${workspaceFolder}"
        }
      }
    ]
  }
  ```
  This differs from the default configuration in that the `PYTHONPATH` is pointing at the top level `workspaceFolder` which allows the code to use the correct module paths (e.g., tasks.eo3assemble).

## Understanding the io_lulc_annual_v02 Product and Data

To create a *Product Definition* and *dataset metadta*, you need to understand two key aspects of your data:
1. What metadata is available for the product?
2. How the organization and format of the data form an individual **dataset** and the **Product** collection as a whole.



This data is originally from a STAC indexed data source freely available on the [Microsoft Planetary Computer and is from the Impact Observatory 10m Annual Land Use Land Cover (9-class) V2 product collection](https://planetarycomputer.microsoft.com/dataset/io-lulc-annual-v02). It is used as an example for local indexing with this copy and there is a matching tutorial for using it directly with ODC via STAC on the ODC github.

### io_lulc_annual_v02 Metadata

There are several forms of available metadata:
1. The [Sentinel Hub collection description](https://custom-scripts.sentinel-hub.com/custom-scripts/other_collections/impact-observatory/)  contains a description of the `io-lulc-annual-v02` collection and a sample Sentinel Hub script for its use.
2. The [Impact Observatory, as the creator of the data, has their own general description page](https://www.impactobservatory.com/10m-land-cover/).
3. The [Impact Observatory also has a more detailed description page](https://docs.impactobservatory.com/lulc-maps/lulc-maps.html)
3. The [MS Planetary Computer has their descroption](https://planetarycomputer.microsoft.com/dataset/io-lulc-annual-v02).
2. The GeoTIFFs contain metadata. You can use `gdalinfo` to inspect the metadata from the GeoTIFF files. This will provide information on `crs`, bounding box, pixel origin location (e.g., center of pixel or upper left corner), NoData value, and data type.
3. The *folder* and *filenames* contain metadata! `15M-2017.tif` is both the UTM zone and the product year.

### Key Points About the Metadata

1. Some metadata is replicated in multiple places.
2. Some metadata requires a tool like `gdalinfo` to access.
3. Some metadata is not specific enough on its own. For example, `15M-2017` is probably the cell and date code. How did I know that? The information is at the bottom of the [Impact Observatory detailed description page](https://docs.impactobservatory.com/tutorials/aws-open-data-exchange/aws-open-data-exchange.html#to-create-an-http-download-url) in the section about the AWS open data exchange.
4. The folder structure and filenames contain metadata, which is very common. For example, Landsat data includes information about collection, level of processing, quality, acquisition date, and processing date in its *filenames*. (e.g., `LC08_L2SP_015036_20150310_20200909_02_T1_SR`)
5. Some metadata may be absent, such as license information.
6. Some metadata is in a picture or pdf format. Example, at first glance it looks like the land cover class definitions are available as a [colour legend](https://docs.impactobservatory.com/lulc-maps/lulc-maps.html#land-cover-classes). In practice a little further down the [colours are shown mapped to words](https://docs.impactobservatory.com/lulc-maps/lulc-maps.html#lulc-class-colors) and the `gdalinfo` for the tifs shows mapping of the integer values to colours in a colour table.

### Goals

1. Obtain the _required_ metadata for a valid *eo3* base *Product Definition*.
2. Optionally, add as much (or as little) additional metadata as you like.

### Reconciling Differences

You may need to reconcile differences between replicated metadata values. For example, what if the `NoData` values in the product webpage don't match those returned by `gdalinfo` on the individual files? This can happen!

**Tip:** When reconciling differences, consider how these components are generated and human behavior. The `NoData` values in the README file are in an image and document, which is more effort to update manually. The `NoData` values in the individual files were likely created programmatically at the same time as the data. Chances are, the data uses the `NoData` values embedded in the GeoTIFF metadata. Generally, the closer the metadata is to the data, the more likely it was part of the processing stage, and the documentation is still catching up.

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

## Creating a *Product Definition*

Now that we understand our data and metadata, and have made some choices, we can create the *Product Definition*. The `yaml` snippet below includes comments on where the `values` come from, which you should be able to locate given the above discussion.

```yaml
name: io_lulc_annual_v02 # common shorthand used in several metadata docs.
description: Time series of annual global maps of land use and land cover (LULC). It currently has data from 2017-2023. The maps are derived from ESA Sentinel-2 imagery at 10m resolution. Each map is a composite of LULC predictions for 9 classes throughout the year in order to generate a representative snapshot of each year. # from the Planetary computer abstract
metadata_type: eo3 # it's an eo3 compliant product definition

measurements:
- name: land_cover_class # from the detailed product description
  nodata: 0 # from the gdalinfo (better source) and verified it matches the detailed product description
  dtype: uint8 # from the gdalinfo (better source) and verified it matches the detailed product description
...
```

This is okay and it will work, but we can improve on it:

```yaml
name: io_lulc_annual_v02 # common shorthand used in several metadata docs.
description: Time series of annual global maps of land use and land cover (LULC). It currently has data from 2017-2023. The maps are derived from ESA Sentinel-2 imagery at 10m resolution. Each map is a composite of LULC predictions for 9 classes throughout the year in order to generate a representative snapshot of each year. # from the Planetary computer abstract
metadata_type: eo3 # it's an eo3 compliant product definition
license: CC-BY-4.0 # added a License from https://docs.impactobservatory.com/legal.html#maps-for-good.

# This section is necessary for ODC 1.8 - you'd be forgiven for not noticing the implementation note in the spec.
metadata:
  product:
    name: io_lulc_annual_v02 # must match the name above

measurements:
- name: land_cover_class # from the detailed product description
  aliases: [LCC, cover_class, class] # Aliases are used for alternative forms.
  units: 1 # required field - 1 is a dimensionless unit
  nodata: 0 # from the gdalinfo (better source) and verified it matches the detailed product description
  dtype: uint8 # from the gdalinfo (better source) and verified it matches the detailed product description
```

The full sample *Product Definition* can be found in [`../products/impact_observatory/io_lulc_annual_v02.yaml`](../products/impact_observatory/io_lulc_annual_v02.yaml).

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
