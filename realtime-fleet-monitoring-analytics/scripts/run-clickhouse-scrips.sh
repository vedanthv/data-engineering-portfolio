#!/bin/bash

CONTAINER=clickhouse

DDL_DIR=./clickhouse-ddls/base

echo "Executing all ClickHouse DDL files in $DDL_DIR..."

# Run inside the container
sudo docker compose exec -T $CONTAINER bash -c "
    for file in \$(ls $DDL_DIR/*.sql | sort); do
        echo \"------------------------------------------\"
        echo \"Running DDL: \$file\"
        echo \"------------------------------------------\"
        clickhouse-client --multiquery < \"\$file\"
        echo \"Done: \$file\"
        echo
    done
"

echo "All ClickHouse DDL files executed successfully."
