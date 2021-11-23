#!/bin/bash

files="README.md CONTRIBUTING.md src/charm.py tests/unit/test_charm.py tests/integration/test_charm.py metadata.yaml"

mkdir -p lib/charms

for file in $files; do
    sed -i $file -e "s/CharmName/UpdateDB/g"
    sed -i $file -e "s/charm-name/update-db/g"
    sed -i $file -e "s/charm_name/update_db/g"
    sed -i $file -e "s/Charm Name/Update DB/g"
    sed -i $file -e "s/<image>/ubuntu:latest/g"

done

tox -e fmt
tox
