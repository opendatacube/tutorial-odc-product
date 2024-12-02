#!python

import os
import configparser
import subprocess
import click

@click.command()
@click.argument('product', type=str)
@click.argument('dc_env', type=str)
@click.option(
    '-o','--ows_env', type=str,
    default = None,
    help = 'Optional OWS db specific environment if different'
)
@click.option(
    '-c', '--config_path',
    type = click.Path(file_okay = True, dir_okay = False, readable = True),
    default = None,
    help = 'Load ODC config from this file. Default location is your home directory.'
)
@click.option(
    '-s', '--scripts',
    type = click.Path(file_okay = False, dir_okay = True, readable = True),
    default = None,
    help = 'Path to the odc-product-delete folder containing the SQL scripts. Default is current working directory.'
)
@click.option(
    '--accept',
    is_flag = True,
    default = False,
    show_default = True,
    help = 'Say [Y]es to the "Are you sure?" question'
)
def cli(product, dc_env, ows_env: str = None, config_path: str = None, scripts: str = None, accept: bool = False):
    """Delete a product from an ODC database.
    Select the target database and (admin) credentials with the ODC environment label (in the datacube config file).
    Requires a copy of https://github.com/opendatacube/datacube-dataset-config.
    """

    if config_path is None:
        config_path = os.path.expanduser('~/.datacube.conf')

    config = configparser.ConfigParser()
    config.read_file(open(config_path))  # Should raise if not readable
    dbhost = config.get(dc_env, 'db_hostname')
    dbname = config.get(dc_env, 'db_database')
    dbuser = config.get(dc_env, 'db_username')
    dbpass = config.get(dc_env, 'db_password')

    if scripts is None:
        scripts = os.path.expanduser('.')

    os.chdir(f'{scripts}/odc-product-delete')  # Should raise if can't chdir

    base = [f'PGPASSWORD={dbpass}', 'psql',
        '-U', dbuser, '-d', dbname, '-h', dbhost,
        '-v', f'product_name={product}']

    if accept != True:
        ans = input(f'Delete "{product}" from datacube env "{dc_env}". Are you sure (y)? ')
        if ans not in ('y', 'Y'):
            exit(0)

    explorer_odc_sql_file = [
        'delete_odc_product_explorer.sql',  # Delete from Explorer
        'delete_odc_product.sql',           # Delete from ODC
        'cleanup_explorer.sql',             # Clean up Explorer views
        'cleanup_odc_indexes.sql',          # Clean up ODC indexes
    ]
    ows_sql_file = ['delete_odc_product_ows.sql'] # Delete from OWS, can fail don't worry

    if ows_env is None:
        sql_files = ows_sql_file.extend(explorer_odc_sql_file)
    else:
        sql_files = explorer_odc_sql_file

    if ows_env is not None:
        ows_dbhost = config.get(ows_env, 'db_hostname')
        ows_dbname = config.get(ows_env, 'db_database')
        ows_dbuser = config.get(ows_env, 'db_username')
        ows_dbpass = config.get(ows_env, 'db_password')

        ows_base = [f'PGPASSWORD={ows_dbpass}', 'psql',
        '-U', ows_dbuser, '-d', ows_dbname, '-h', ows_dbhost,
        '-v', f'product_name={product}']

        print(f'=== OWS Delete Product: {product} ===')

        cmd = ows_base + ['-f', 'delete_odc_product_ows.sql']

        subprocess.run(' '.join(cmd), shell=True, check=True)

    print(f'=== Product: {product} ===')
    for k in sql_files:
        print(f'=== Run: {k} ===')
        cmd = base + ['-f', k]
        subprocess.run(' '.join(cmd), shell=True, check=True)
        # print(' '.join(cmd))
        # print()

if __name__ == "__main__":
    cli()
