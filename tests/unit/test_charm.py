# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import pytest

# from ops.model import ActiveStatus, MaintenanceStatus
from ops.testing import Harness
from pytest_mock import MockerFixture

from charm import UpgradeDBCharm


@pytest.fixture
def harness(mocker: MockerFixture):
    update_db_harness = Harness(UpgradeDBCharm)
    update_db_harness.begin()
    yield update_db_harness
    update_db_harness.cleanup()
