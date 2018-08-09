# (C) Copyright 2018 Enthought, Inc., Austin, TX
# All rights reserved.
#
# The code in the ci/ package is proprietary and should not be redistributed
# without explicit approval.

"""
Utilities for setting up a development environment and running tests.  See
the top-level repository README for more detailed instructions on how to use
these.
"""
from __future__ import absolute_import, print_function, unicode_literals

import contextlib
import os
import shutil
import stat
import tempfile

import click

import ci.config as cfg
from ci.python_environment import (
    current_platform,
    PythonEnvironment,
)

# Click will complain about unicode_literals unless we disable the warning.
# Ref: http://click.pocoo.org/5/python3/#unicode-literals
click.disable_unicode_literals_warning = True


# Common options for the commands.
python_version_option = click.option(
    "--python-version",
    type=click.Choice(cfg.PYTHON_VERSIONS),
    help="Python version for the development environment.",
    default=cfg.DEFAULT_PYTHON,
    show_default=True,
    envvar="CI_PYTHON_VERSION",
)
toolkit_option = click.option(
    "--toolkit",
    type=click.Choice(cfg.TOOLKITS),
    help="UI toolkit for the development environment.",
    default=cfg.DEFAULT_TOOLKIT,
    show_default=True,
    envvar="CI_TOOLKIT",
)
verbose_option = click.option(
    "--verbose/--quiet",
    help="Run tests in verbose mode?  [default: --verbose]",
    default=True,
)


# All commands are implemented as subcommands of the cli group.
@click.group()
def cli():
    """
    Development and continuous integration helpers for Traits Futures.
    """
    pass


@cli.command()
@python_version_option
@toolkit_option
@click.option(
    "--editable/--not-editable", default=False,
    help="Install traits_futures in editable mode?  [default: --not-editable]"
)
def build(python_version, toolkit, editable):
    """
    Create an EDM-based development environment.
    """
    pyenv = _get_devenv(python_version, toolkit)
    platform = current_platform()
    dependencies = _core_dependencies(platform, python_version, toolkit)

    # Destroy any existing environment.
    if pyenv.exists():
        pyenv.destroy()

    # Create new environment and populate with dependent packages.
    pyenv.create()
    pyenv.install(dependencies)

    # Install the local package, ignoring dependencies declared in its
    # setup.py.
    pip_cmd = ["-m", "pip", "install", "--no-deps"]
    if editable:
        pip_cmd.append("--editable")
    pip_cmd.append(".")
    pyenv.python(pip_cmd)

    click.echo("Created environment with name {}".format(
        pyenv.environment_name))


@cli.command()
@python_version_option
@toolkit_option
@verbose_option
@click.option(
    "--branch/--no-branch",
    help="Include branch coverage?  [default: --branch]",
    default=True,
)
@click.option(
    "--html/--no-html",
    help="Create an HTML report?  [default: --html]",
    default=True,
)
@click.option(
    "--report/--no-report",
    help="Output report to the console?  [default: --report]",
    default=True,
)
def coverage(python_version, toolkit, verbose, branch, html, report):
    """
    Run the test suite under coverage.
    """
    pyenv = _get_devenv(python_version, toolkit)

    test_cmd = ["-m", "unittest", "discover"]
    if verbose:
        test_cmd.append("--verbose")
    test_cmd.append(cfg.PACKAGE_NAME)

    coverage_cmd = [
        "-m", "coverage", "run",
        "--source", cfg.PACKAGE_NAME,
    ]
    if branch:
        coverage_cmd.append("--branch")

    # Run coverage from an empty directory.
    with in_coverage_directory():
        return_code = pyenv.python_return_code(coverage_cmd + test_cmd)
        if html:
            pyenv.python(["-m", "coverage", "html"])
        if report:
            pyenv.python(["-m", "coverage", "report"])
            click.echo()

    if return_code:
        raise click.ClickException("There were test failures.")
    else:
        click.echo("All tests passed.")


@cli.command()
@python_version_option
@toolkit_option
def doc(python_version, toolkit):
    """
    Run documentation build.
    """
    pyenv = _get_devenv(python_version, toolkit)

    # Be nitpicky. This detects missing class references.
    sphinx_options = ["-n"]

    build_cmd = ["-m", "sphinx"]
    build_cmd.extend(sphinx_options)
    build_cmd.extend([cfg.DOCS_SOURCE_DIR, cfg.DOCS_BUILD_DIR])
    pyenv.python(build_cmd)


@cli.command()
@python_version_option
@toolkit_option
@click.argument(
    "example-name",
    type=click.Choice(cfg.EXAMPLES),
)
def example(python_version, toolkit, example_name):
    """
    Run one of the examples.
    """
    pyenv = _get_devenv(python_version, toolkit)
    example_script = os.path.join("examples", cfg.EXAMPLES[example_name])
    pyenv.python([example_script])


@cli.command()
@python_version_option
@toolkit_option
def flake8(python_version, toolkit):
    """
    Run flake8 on all Python files.
    """
    targets = cfg.FLAKE8_TARGETS

    pyenv = _get_devenv(python_version, toolkit)
    if pyenv.python_return_code(["-m", "flake8"] + targets):
        click.echo()
        raise click.ClickException("Flake8 check failed.")
    else:
        click.echo("Flake8 check succeeded.")


@cli.command()
@python_version_option
@toolkit_option
@verbose_option
def test(python_version, toolkit, verbose):
    """
    Run the test suite.
    """
    pyenv = _get_devenv(python_version, toolkit)

    test_cmd = ["-m", "unittest", "discover"]
    if verbose:
        test_cmd.append("--verbose")
    test_cmd.append(cfg.PACKAGE_NAME)

    # Run tests from an empty directory to avoid picking up
    # code directly from the repository instead of the target
    # environment.
    with in_test_directory():
        return_code = pyenv.python_return_code(test_cmd)

    if return_code:
        raise click.ClickException("There were test failures.")
    else:
        click.echo("All tests passed.")


# Helper functions ############################################################

def _get_devenv(python_version, toolkit):
    """
    Return a PythonEnvironment corresponding to the development environment for
    a given Python version and UI toolkit.
    """
    platform = current_platform()
    if (platform, python_version, toolkit) not in cfg.PLATFORMS:
        raise click.ClickException(
            "Unsupported configuration: platform={platform}, "
            "python_version={python_version}, toolkit={toolkit}".format(
                platform=platform,
                python_version=python_version,
                toolkit=toolkit,
            )
        )

    runtime_version = cfg.RUNTIME_VERSION[python_version]
    environment_name = cfg.ENVIRONMENT_TEMPLATE.format(
        prefix=cfg.PREFIX,
        python_version=python_version,
        toolkit=toolkit,
    )

    return PythonEnvironment(
        edm_config=cfg.EDM_CONFIGURATION,
        name=environment_name,
        runtime_version=runtime_version,
    )


def _remove_readonly(func, path, _):
    """ Clear the readonly bit and reattempt the removal """
    os.chmod(path, stat.S_IWRITE)
    func(path)


@contextlib.contextmanager
def in_test_directory():
    """
    Change to a temporary empty directory for testing purposes.
    """
    old_cwd = os.getcwd()
    tempdir = tempfile.mkdtemp()
    os.chdir(tempdir)
    try:
        yield
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(tempdir, onerror=_remove_readonly)


@contextlib.contextmanager
def in_coverage_directory():
    """
    Temporarily change to the coverage directory.
    """
    # Delete old directory if necessary.
    coverage_directory = cfg.COVERAGE_DIR
    if os.path.exists(coverage_directory):
        shutil.rmtree(coverage_directory, onerror=_remove_readonly)
    os.makedirs(coverage_directory)

    old_cwd = os.getcwd()
    os.chdir(coverage_directory)
    try:
        yield
    finally:
        os.chdir(old_cwd)


def _core_dependencies(platform, python_version, toolkit):
    """
    Compute core dependencies for the given platform, Python version and
    toolkit.
    """
    # Make a copy to avoid accidentally mutating the cfg.CORE_DEPS global.
    dependencies = list(cfg.CORE_DEPS)
    dependencies.extend(cfg.VERSION_CORE_DEPS.get(python_version, []))
    dependencies.extend(cfg.TOOLKIT_CORE_DEPS.get(toolkit, []))
    return dependencies


if __name__ == "__main__":
    cli()
