#!/bin/bash

CONTAINER=sql-client

DDL_DIR=/opt/flink/usrlib
DDL_FILE=flink-transforms.sql  

docker compose exec -T $CONTAINER bash -c "
    /opt/flink/bin/sql-client.sh \
        -l $DDL_DIR \
        -f $DDL_DIR/$DDL_FILE
"
