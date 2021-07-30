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

# XXX Fix case where there's nothing to commit
# XXX Do sanity check on doc_version: should be either "dev"
# or "major.minor"; nothing else
# XXX Merge with ci module. (Or make new module? Or keep this as it is, as
#    a script?)
# XXX Command-line arguments (argparse?)

import argparse
import base64
import contextlib
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile

#: Path to git executable
GIT = "git"

#: URL for the upstream GitHub repository.
UPSTREAM = "https://github.com/enthought/traits-futures"


ROOT_DIR = os.path.abspath(".")
DOCS_SOURCE_DIR = os.path.join(ROOT_DIR, "docs", "source")


DOC_BRANCH = "gh-pages-testing"
DOC_SUBFOLDER = "dev"


def join(split_command):
    """Return a shell-escaped string from *split_command*."""
    # This can be replaced with shlex.join for Python >= 3.8.
    return " ".join(shlex.quote(arg) for arg in split_command)


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


def run_git(*cmd):
    """
    Run the given git command in a subprocess.
    """
    git_cmd = [GIT, *cmd]
    print(join(git_cmd))
    subprocess.run([GIT, *cmd], check=True)


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
        run_git("init")
        run_git("remote", "add", "origin", repo)
        run_git("fetch", "--no-tags", "--prune", "--depth=1", "origin", branch)
        run_git("checkout", branch)
    return clone_directory


def push_updates(clone_directory, doc_version, branch, token):
    # Access token
    # - needs public_repo only?

    b64_token = base64.b64encode(token.encode("ascii")).decode("ascii")

    with current_directory(clone_directory):
        # Stage the changes
        run_git("add", doc_version)
        commit_message = "Automated update of documentation"
        run_git("commit", "-m", commit_message)
        run_git(
            "-c",
            f"http.https://github.com/.extraheader=AUTHORIZATION: basic {b64_token}",
            "push",
            "origin",
            branch,
        )


def build_html_docs(source_dir, target_directory, name):
    build_dir = os.path.join(target_directory, name)
    with temporary_directory() as doctrees_dir:
        sphinx_cmd = [
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
        subprocess.run(sphinx_cmd, check=True)
        return build_dir


def replace_tree(source, target):
    if os.path.exists(target):
        shutil.rmtree(target, onerror=_remove_readonly)
    os.rename(source, target)


def main(doc_version, token):
    with temporary_directory() as temp_dir:
        # Check GIT version, for the record.
        subprocess.run([GIT, "version"], check=True)

        docs_build_dir = build_html_docs(DOCS_SOURCE_DIR, temp_dir, "build")
        docs_gh_pages = clone_branch(
            UPSTREAM, DOC_BRANCH, temp_dir, "traits-futures"
        )
        replace_tree(docs_build_dir, os.path.join(docs_gh_pages, doc_version))
        push_updates(docs_gh_pages, doc_version, DOC_BRANCH, token)


def main():
    parser = argparse.ArgumentParser(
        description="Build and upload documentation"
    )
    parser.add_argument("-t", "--token", help="Authorization token for GitHub")
    parser.add_argument(
        "version",
        help="major.minor version to update documentation for, for example 3.1",
    )
    args = parser.parse_args()

    # Retrieve the token
    if args.token is None:
        print("Attempting to retrieve token from GITHUB_TOKEN")
        token = os.environ.get("GITHUB_TOKEN", "")
    else:
        token = args.token
    if not token:
        print(
            "A GitHub authentication token is required. "
            "Use the --token argument or set the "
            "GITHUB_TOKEN environment variable."
        )
        sys.exit(1)
    else:
        print(token)

    # Validate the version



if __name__ == "__main__":
    main()
    # token = os.environ["GITHUB_TOKEN"]
    # main(doc_version="7.5", token=token)
