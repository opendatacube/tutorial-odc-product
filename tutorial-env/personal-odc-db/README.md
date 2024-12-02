# Running a personal ODC Database

Working with the ODC Database requires write access to create new Products and Datasets. This can be challenging when dealing with large amounts of new data or data intended for distribution, especially on a shared system. To avoid permission issues and impact, we can run our own private PostgreSQL server for ODC during development.

Here's how to get PostgreSQL installed for private use:

Steps:

1. [Install micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html#automatic-install)

  ``` bash
  $ "${SHELL}" <(curl -L micro.mamba.pm/install.sh)
  ```

  Accept the installation defaults, then:

  ``` bash
  $ source ~/.bashrc
  ```


2. Download and install PostgreSQL into ~/postgresql.

  ``` bash
  $ micromamba create --prefix ~/postgresql --yes postgresql
  ```

3. Initialise a Postgres Data Dir, Launch Postgres locally, and create an empty datacube DB.

  ``` bash
  $ ./tutorial-env/personal-odc-db/db.sh init
  ```

4. Set ODC environment variables and initialise an ODC Database.

  ``` bash
  $ eval "$(./tutorial-env/personal-odc-db/db.sh env)"
  $ datacube system init
  ```
