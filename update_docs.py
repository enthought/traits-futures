# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Simple Python script to update the gh-pages documentation.
"""

import base64
import contextlib
import os
import shutil
import stat
import subprocess
import tempfile

DOCS_SOURCE_DIR = "docs/source"
GIT = "git"
UPSTREAM = "https://github.com/enthought/traits-futures"
DOC_BRANCH = "gh-pages-testing"
DOC_SUBFOLDER = "dev"


def _remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


@contextlib.contextmanager
def temporary_directory():
    tempdir = tempfile.mkdtemp()
    try:
        yield tempdir
    finally:
        shutil.rmtree(tempdir, onerror=_remove_readonly)


@contextlib.contextmanager
def current_directory(directory):
    old_cwd = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(old_cwd)


def clone_branch(repo, branch, target_directory, name):
    """
    Make a shallow clone of a particular branch from upstream.

    Parameters
    ----------
    repo : str
        URL of the upstream repository.
    branch : str
        Name of the branch to clone.
    target_directory : str
        Directory to clone into. This directory should already exist.
    name : str
        Name of the subdirectory to clone into. A directory with this name
        will be created.
    """
    clone_directory = os.path.join(target_directory, name)
    os.mkdir(clone_directory)
    with current_directory(clone_directory):
        subprocess.run([GIT, "init"], check=True)
        subprocess.run([GIT, "remote", "add", "origin", repo], check=True)
        subprocess.run(
            [
                GIT,
                "fetch",
                "--no-tags",
                "--prune",
                "--depth=1",
                "origin",
                branch,
            ],
            check=True,
        )
        subprocess.run([GIT, "checkout", branch], check=True)
    return clone_directory


def push_updates(clone_directory, doc_version, branch, token):
    # Access token
    # - needs public_repo only?

    b64_token = base64.b64encode(token.encode("ascii")).decode("ascii")

    with current_directory(clone_directory):
        # Stage the changes
        subprocess.run(
            [
                GIT,
                "add",
                doc_version,
            ],
            check=True,
        )
        # Commit the changes
        subprocess.run(
            [GIT, "commit", "-m", "Automated update of documentation"],
            check=True,
        )

        subprocess.run(
            [
                GIT,
                "-c",
                f"http.https://github.com/.extraheader=AUTHORIZATION: basic {b64_token}",
                "push",
                "origin",
                branch,
            ],
            check=True,
        )


def build_html_docs(source_dir, target_directory, name):
    build_dir = os.path.join(target_directory, name)
    with temporary_directory() as doctrees_dir:
        run_sphinx_cmd = [
            "python",
            "-m",
            "sphinx",
            "-b",
            "html",
            # We don't want the doctrees in the published docs, so put them in
            # a temporary directory instead of the build directory.
            "-d",
            doctrees_dir,
            source_dir,
            build_dir,
        ]
        subprocess.run(
            run_sphinx_cmd,
            check=True,
        )
        return build_dir


def replace_tree(source, target):
    if os.path.exists(target):
        shutil.rmtree(target, onerror=_remove_readonly)
    os.rename(source, target)


def main(doc_version, token):
    # XXX Do sanity check on doc_version: should be either "dev"
    # or "major.minor"; nothing else
    with temporary_directory() as temp_dir:
        # Check GIT version, for the record.
        subprocess.run([GIT, "version"], check=True)

        docs_build_dir = build_html_docs(DOCS_SOURCE_DIR, temp_dir, "build")
        docs_gh_pages = clone_branch(
            UPSTREAM, DOC_BRANCH, temp_dir, "traits-futures"
        )
        print("Replacing tree")
        replace_tree(docs_build_dir, os.path.join(docs_gh_pages, doc_version))
        print("Pushing updates")
        push_updates(docs_gh_pages, doc_version, DOC_BRANCH, token)


if __name__ == "__main__":
    token = os.environ["GITHUB_OAUTH_TOKEN"]
    assert token
    main(doc_version="7.4", token=token)
