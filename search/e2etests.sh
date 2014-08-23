#!/bin/bash

# add end to end tests manually. We want them to run periodically
# and independently from the unit tests.
# To be much improved: we want a test suite and its report, async.

python datasources/all/discogs/discogsConnectorLiveTest.py
python datasources/frFR/chapitre/tests/e2e/chapitreLiveTest.py
