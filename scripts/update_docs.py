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
Python script to update the gh-pages documentation.
"""

import argparse
import base64
import contextlib
import os
import re
import shlex
import shutil
import stat
import subprocess
import tempfile

#: Path to git executable
GIT = "git"

#: URL for the upstream GitHub repository.
UPSTREAM = "https://github.com/enthought/traits-futures"

#: The name of the branch containing the gh-pages documentation.
#: XXX Change me to gh-pages before merge!
DOC_BRANCH = "gh-pages-testing"

# Identify local directory containing the documentation source.
ROOT_DIR = os.path.abspath(".")
DOCS_SOURCE_DIR = os.path.join(ROOT_DIR, "docs", "source")


def join(split_command):
    """Return a shell-escaped string from *split_command*."""
    # This can be replaced with shlex.join for Python >= 3.8.
    return " ".join(shlex.quote(arg) for arg in split_command)


def _remove_readonly(func, path, _):
    """Helper for shutil.rmtree for removing readonly files."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


@contextlib.contextmanager
def temporary_directory():
    """
    Context manager to create a temporary directory.
    """
    tempdir = tempfile.mkdtemp()
    try:
        yield tempdir
    finally:
        shutil.rmtree(tempdir, onerror=_remove_readonly)


@contextlib.contextmanager
def current_directory(directory):
    """
    Context manager to temporarily change the current working directory.
    """
    old_cwd = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(old_cwd)


def run_git(*cmd, check=True, secrets={}):
    """
    Run the given Git command in a subprocess.

    Also prints the command before execution, while hiding any secrets.

    Parameters
    ----------
    cmd : list
        Arguments to the git command, as strings. The strings may contain
        "{}"-style placeholders, which will be interpolated with values from
        the "secrets" dictionary.
    check : bool, optional
        If True (the default), an exception is raised if the command fails.
        If False, no exception is raised.
    secrets : dict
        Mapping from secret names to secret values.

    Returns
    -------
    rc : int
        The return code from the git command.
    """
    # Version used for printing, replacing secret values with asterisks.
    hidden = dict.fromkeys(secrets, "***")

    plain_git_cmd = [GIT, *(entry.format_map(secrets) for entry in cmd)]
    redacted_git_cmd = [GIT, *(entry.format_map(hidden) for entry in cmd)]

    print(join(redacted_git_cmd))
    return subprocess.run(plain_git_cmd, check=check).returncode


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
    """
    Stage, commit and push documentation updates.

    Parameters
    ----------
    clone_directory : str
        The directory containing the Git clone of the repository.
    doc_version : str
        The subdirectory for the documentation update.
    branch : str
        The branch to push to
    token : str
        The GitHub authorization token. This should have the "public_repo"
        scope. It doesn't need any other scopes.
    """
    secrets = dict(
        b64_token=base64.b64encode(token.encode("ascii")).decode("ascii")
    )
    with current_directory(clone_directory):
        # Stage the changes
        run_git("add", doc_version)

        # If there's nothing to commit, stop.
        rc = run_git("diff-index", "--quiet", "--cached", "HEAD", check=False)
        if not rc:
            print("No changes in built documentation. Nothing to do.")
            return
        elif rc != 1:
            raise RuntimeError(
                f"diff-index command failed with return code {rc}"
            )

        commit_message = "Automated update of documentation"
        run_git("commit", "-m", commit_message)
        run_git(
            "-c",
            (
                "http.https://github.com/.extraheader=AUTHORIZATION: "
                "basic {b64_token}"
            ),
            "push",
            "origin",
            branch,
            secrets=secrets,
        )


def build_html_docs(source_dir, target_directory, name):
    """
    Build the HTML documentation tree.

    Parameters
    ----------
    source_dir : str
        Path to the directory containing the documentation source.
    target_directory : str
        Path to the directory to place the built documentation in.
        This directory should already exist.
    name : str
        Name of the source build directory, as a subdirectory of the
        target_directory. This directory will be created.
    """

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
    """
    Replace the target directory with the contents of the source directory.

    If the target directory does not yet exist, it will be created. If it
    does exist, its contents will first be discarded.

    Parameters
    ----------
    source : str
        Path to the source directory.
    target : str
        Path to the target directory.
    """
    if os.path.exists(target):
        shutil.rmtree(target, onerror=_remove_readonly)
    os.rename(source, target)


def build_and_upload_docs(doc_version, token):
    """
    Build and upload the documentation.

    Builds documentation from the current working tree, and uploads the
    built documentation to a subdirectory in the gh-pages branch.

    Parameters
    ----------
    doc_version : str
        The subdirectory to upload to. This should either be 'dev', or have the
        form "major.minor". If the subdirectory already exists in gh-pages, the
        current contents will be overwritten. If it doesn't exist, it will be
        created.
    token : str
        GitHub authorization token.
    """
    # Print git version for the benefit of the log.
    run_git("version")
    with temporary_directory() as temp_dir:
        docs_build_dir = build_html_docs(DOCS_SOURCE_DIR, temp_dir, "build")
        docs_gh_pages = clone_branch(
            UPSTREAM, DOC_BRANCH, temp_dir, "traits-futures"
        )
        replace_tree(docs_build_dir, os.path.join(docs_gh_pages, doc_version))
        push_updates(docs_gh_pages, doc_version, DOC_BRANCH, token)


#: Regex for valid versions
VERSION_REGEX = re.compile(r"\A(\d+\.\d+|dev)\Z")

#: Description for the script.
DESCRIPTION = """Build documentation and deploy to gh-pages branch."""


def main():
    """
    Parse arguments and dispatch to the main documentation build.
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "-t",
        "--token",
        default=os.environ.get("GITHUB_TOKEN", ""),
        help="Authorization token for GitHub",
    )
    parser.add_argument(
        "version",
        help="major.minor version to update documentation for, for example 3.1",
    )
    args = parser.parse_args()

    # Retrieve and validate the token
    token = (
        args.token
        if args.token is not None
        else os.environ.get("GITHUB_TOKEN", "")
    )
    if token == "":
        parser.error("no token provided, and GITHUB_TOKEN is not defined")

    # Validate the version
    version = args.version.lower()
    if not VERSION_REGEX.match(version):
        parser.error("version should be 'dev' or have the form 12.34")

    build_and_upload_docs(version, token)


if __name__ == "__main__":
    main()
