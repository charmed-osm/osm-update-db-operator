<!-- Copyright 2021 Canonical Ltd.
See LICENSE file for licensing details. -->

# OSM Update DB Operator

[![code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black/tree/main)

## Description

Charm used to update the OSM databases during an OSM upgrade process. To be used you should have an instance of OSM running that you may want to upgrade

## Usage

### Deploy the charm (locally)

Clone the repository:

```shell
git clone https://github.com/gcalvinos/db-upgrade-operator.git
cd db-upgrade-operator
```

Build and deploy the charm:

```shell
sudo snap install charmcraft
charmcraft build
juju add-model update-db
juju deploy ./osm-update-db_ubuntu-20.04-amd64.charm
```

Set MongoDB and MySQL URIs:

```shell
juju config osm-update-db mysql-uri=<mysql_uri>
juju config osm-update-db mongodb-uri=<mongodb_uri>
```

### Updating the databases

In case we want to update both databases, we need to run the following command:

```shell
juju run-action osm-update-db/0 update-db current-version=<Number_of_current_version> target-version=<Number_of_target_version>
# Example:
juju run-action osm-update-db/0 update-db current-version=9 target-version=10
```

In case only you just want to update MongoDB, then we can use a flag 'mongodb-only=True':

```shell
juju run-action osm-update-db/0 update-db current-version=9 target-version=10 mongodb-only=True
```

In case only you just want to update MySQL database, then we can use a flag 'mysql-only=True':

```shell
juju run-action osm-update-db/0 update-db current-version=9 target-version=10 mysql-only=True
```

You can check if the update of the database was properly done checking the result of the command:

```shell
juju show-action-output <Number_of_the_action>
```

### Fixes for bugs

Updates de database to apply the changes needed to fix a bug. You need to specify the bug number. Example:

```shell
juju run-action osm-update-db/0 apply-patch bug-number=1837 
```

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines
on enhancements to this charm following best practice guidelines, and
`CONTRIBUTING.md` for developer guidance.
