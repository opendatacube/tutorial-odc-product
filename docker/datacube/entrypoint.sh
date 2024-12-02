#!/bin/bash
set -e

# Wait for the database to be ready
until PGPASSWORD=$DB_PASSWORD psql -h $DB_HOSTNAME -U $DB_USERNAME -d $DB_DATABASE -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"

# Initialize the database if it doesn't exist
. /env/bin/activate
datacube system init
datacube system check

# Execute the provided command
exec "$@"