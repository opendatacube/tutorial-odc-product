#!/bin/bash

# Directory containing metadata files
METADATA_DIR="/home/ubuntu/odc-product-tutorial/data"

# Loop over each file in the metadata directory
for metadata_file in "$METADATA_DIR"/*.yaml; do
  # Check if the file is a regular file
  if [[ -f "$metadata_file" ]]; then
    echo "Adding product from metadata file: $metadata_file"
    # Run the datacube product add command
    datacube dataset add "$metadata_file"
  else
    echo "Skipping non-regular file: $metadata_file"
  fi
done