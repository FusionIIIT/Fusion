T#!/bin/bash

branches=("os-2" "os-3" "os-4")

db_dump=fusiondb_07feb23.sql

for branch in "${branches[@]}"
do
    IFS=' ' read -r name <<< "$branch"
    echo "Connecting fusiondb_07feb23 to $dir"

        cd "$name"
        sudo docker exec -i "$name"_db_1 psql -U fusionuser -d fusiondb < ../../$db_dump
        cd ..

    echo "Connected DB dump to $name"
done
