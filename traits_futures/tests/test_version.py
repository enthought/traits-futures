# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

import re
import unittest

import traits_futures.version

# Regex matching a version number of one of the two forms
#
#   <nnn>.<nnn>.<nnn>
#
# or
#
#   <nnn>.<nnn>.<nnn>.dev<nnn>
#
# We may want to relax the format in the future for alphas, betas and the like.

VERSION_MATCHER = re.compile(r"\A\d+\.\d+.\d+(?:\.dev\d+)?\Z")


class TestVersion(unittest.TestCase):
    def test_version_string(self):
        version = traits_futures.version.version
        self.assertIsInstance(version, str)
        match = VERSION_MATCHER.match(version)
        self.assertIsNotNone(
            match, msg="{!r} appears to be an invalid version".format(version)
        )

    def test_top_level_package_version(self):
        self.assertEqual(
            traits_futures.__version__, traits_futures.version.version
        )
