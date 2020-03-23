# -*- coding: utf-8 -*-

import pytest
import os

DBNAME = "/tmp/test.db"


@pytest.fixture(scope="function")
def clean_dbfile():
    yield
    os.unlink(DBNAME)
