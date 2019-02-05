# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

from __future__ import absolute_import, print_function, unicode_literals

import re
import unittest

import six

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
        self.assertIsInstance(version, six.text_type)
        match = VERSION_MATCHER.match(version)
        self.assertIsNotNone(
            match, msg="{!r} appears to be an invalid version".format(version))

    def test_top_level_package_version(self):
        self.assertEqual(
            traits_futures.__version__, traits_futures.version.version)
