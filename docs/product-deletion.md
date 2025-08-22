## When it all goes wrong - Removing the Product from the Index

The ODC doesn't have a product deletion tool (shock horror!). Members of the ODC community have contributed scripts to manually delete an entire ODC Product and related records in ODC, Explorer, and OWS DB. The SQL scripts need to be applied in a specific order (see the [`README.md`](../tools/odc-product-delete/README.md)) and require ODC database administration privileges in the `.datacube-conf` for all tables to be removed. The EASI [`tools/delete_product.py`](../tools/delete_product.py) CLI utility simplifies this process. If all permissions are in place, running the script with the name of the product will remove it after confirmation.

You may see a few errors in the SQL if the OWS and Explorer tables haven't been initialized yet. This can occur during initial product creation if you start indexing a product and discover a mistake and need to start over before running the `cubedash-gen` and `datacube-ows-update` commands. Those errors can safely be ignored under those conditions.

For the tutorial you can of course just delete the entire local database using the command described earlier.