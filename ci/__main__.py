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
from __future__ import absolute_import, division, print_function

import contextlib
import os
import shutil
import stat
import subprocess

import click
import yaml

import ci.config as cfg
from ci.python_environment import (
    current_platform,
    edm_is_embedded,
    PythonEnvironment,
)


# All commands are implemented as subcommands of the cli group.
@click.group()
def cli():
    """
    Build and continuous integration system.
    """
    pass


# Common options for the commands.
python_version_option = click.option(
    "--python-version", default=cfg.DEFAULT_PYTHON,
    type=click.Choice(cfg.PYTHON_VERSIONS),
    show_default=True,
    envvar="CI_PYTHON_VERSION",
    help="Python version for the development environment",
)
toolkit_option = click.option(
    "--toolkit", default=cfg.DEFAULT_TOOLKIT,
    type=click.Choice(cfg.TOOLKITS),
    show_default=True,
    envvar="CI_TOOLKIT",
    help="UI toolkit for the development environment",
)


@cli.command(name='build')
@python_version_option
@toolkit_option
def build(python_version, toolkit):
    """
    Create an EDM-based development environment.
    """
    # Destroy any existing devenv.
    pyenv = _get_devenv(python_version, toolkit)
    if pyenv.exists():
        pyenv.destroy()

    bundle_file = _bundle_path(current_platform(), python_version, toolkit)
    pyenv.create_from_bundle(bundle_file)

    # Print a summary of EDM config info; this can be useful when debugging CI
    # configuration issues.
    pyenv.edm_info()

    # Install the local packages using pip.
    pyenv.python(['-m', 'pip', 'install', '--no-deps', '--editable', '.'])


@cli.command()
@python_version_option
@toolkit_option
def flake8(python_version, toolkit):
    """
    Run flake8 on all Python files.
    """
    targets = cfg.FLAKE8_TARGETS

    pyenv = _get_devenv(python_version, toolkit)
    if pyenv.python_return_code(['-m', 'flake8'] + targets):
        click.echo()
        raise click.ClickException("Flake8 check failed.")
    else:
        click.echo("Flake8 check succeeded.")


@cli.command()
@python_version_option
@toolkit_option
def test(python_version, toolkit):
    """
    Run the test suite.
    """
    packages = [cfg.PACKAGE_NAME]

    pyenv = _get_devenv(python_version, toolkit)

    packages_with_failures = []
    for package in packages:
        click.echo("Testing {!r} package.\n".format(package))
        cmd = [
            "-m", "unittest", "discover",
            "-v",
            "-t", ".",
            "-s", package,
        ]
        if pyenv.python_return_code(cmd):
            packages_with_failures.append(package)
        click.echo()

    if packages_with_failures:
        msg = "The following packages had test failures: {}.".format(
            ', '.join(packages_with_failures))
        raise click.ClickException(msg)
    else:
        click.echo("All tests passed.")


@cli.command()
@python_version_option
@toolkit_option
@click.option('--branch/--no-branch', default=True,
              help="Include branch coverage? (Default: --branch.)")
@click.option('--html/--no-html', default=True,
              help="Create an HTML report? (Default: --html.)")
@click.option('--report/--no-report', default=True,
              help="Output report to the console? (Default: --report.)")
def coverage(python_version, toolkit, branch, html, report):
    """
    Run the test suite, under coverage.
    """
    packages = [cfg.PACKAGE_NAME]

    # Remove current .coverage file, if any.
    if os.path.exists(".coverage"):
        os.unlink(".coverage")

    pyenv = _get_devenv(python_version, toolkit)

    packages_with_failures = []
    for package in packages:
        click.echo("Testing {!r} package under coverage.\n".format(package))
        test_cmd = [
            "-m", "unittest", "discover",
            "-v",
            "-t", ".",
            "-s", package,
        ]
        run_cmd = [
            "-m", "coverage", "run",
            "--append",
        ] + ["--branch"] * branch
        cmd = run_cmd + test_cmd
        if pyenv.python_return_code(cmd):
            packages_with_failures.append(package)
        click.echo()

    if report:
        pyenv.python(['-m', 'coverage', 'report'])
        click.echo()

    if html:
        pyenv.python(['-m', 'coverage', 'html'])

    if packages_with_failures:
        msg = "The following packages had test failures: {}.".format(
            ', '.join(packages_with_failures))
        raise click.ClickException(msg)
    else:
        click.echo("All tests passed.")


@cli.command(name='regenerate-bundles')
def regenerate_bundles():
    """
    Regenerate EDM bundles for all platforms listed in PLATFORMS.
    """
    api_token = _get_api_token()
    bundle_script = os.path.join(cfg.SCRIPTS, 'generate_bundle.py')

    with _bundle_generation_environment() as pyenv:
        for platform, python_version, toolkit in cfg.PLATFORMS:
            bundle_file = _bundle_path(platform, python_version, toolkit)
            requirements = _core_dependencies(
                platform, python_version, toolkit)
            pyenv.python(
                [
                    bundle_script,
                    "--config", cfg.EDM_CONFIGURATION,
                    "--api-token", api_token,
                    "--platform", platform,
                    "--bundle-format", "2.0",
                    "--version", cfg.RUNTIME_VERSION[python_version],
                    "--output-file", bundle_file,
                ] + cfg.BUNDLE_MODIFIERS + requirements
            )


# Helper functions ############################################################

def _get_devenv(python_version, toolkit):
    """
    Return a PythonEnvironment corresponding to the development
    environment for the appropriate version of Python.
    """
    runtime_version = cfg.RUNTIME_VERSION[python_version]
    environment_name = cfg.ENVIRONMENT_TEMPLATE.format(
        prefix=cfg.PREFIX,
        python_version=python_version,
        toolkit=toolkit,
    )
    return _get_python_environment(environment_name, runtime_version)


def _core_dependencies(platform, python_version, toolkit):
    """
    Compute core dependencies for the given platform, Python version and
    toolkit.
    """
    # Make a copy to avoid accidentally mutating the cfg.CORE_DEPS global.
    dependencies = list(cfg.CORE_DEPS)
    dependencies.extend(cfg.VERSION_CORE_DEPS.get(python_version, []))
    dependencies.extend(cfg.PLATFORM_CORE_DEPS.get(platform, []))
    dependencies.extend(cfg.TOOLKIT_CORE_DEPS.get(toolkit, []))
    return dependencies


def _bundle_path(platform, python_version, toolkit):
    """
    Path to the appropriate bundle file for the given platform and version.
    """
    bundle_filename = cfg.BUNDLE_TEMPLATE.format(
        prefix=cfg.PREFIX,
        platform=platform,
        python_version=python_version,
        toolkit=toolkit,
    )
    return os.path.join(cfg.BUNDLE, bundle_filename)


def _get_api_token():
    """
    Get an appropriate API token, and warn if there's none available.
    """
    # First try the HATCHER_TOKEN env. var.
    if 'HATCHER_TOKEN' in os.environ:
        return os.environ['HATCHER_TOKEN']

    # Then try the default EDM config file, to see if it's got a token in it.
    config_file = os.path.expanduser('~/.edm.yaml')
    if os.path.exists(config_file):
        with open(config_file, 'r') as config_read:
            edm_config = yaml.load(config_read)

        try:
            return edm_config['authentication']['api_token']
        except KeyError:
            pass

    raise click.ClickException(
        "No api-token found. Please either use 'edm configure' to "
        "set up your access token, or set the HATCHER_TOKEN "
        "environment variable."
    )


def _get_python_environment(name, runtime_version,
                            edm_config=cfg.EDM_CONFIGURATION):
    """
    Get a Python environment for a given configuration.
    """
    api_token = _get_api_token()

    kwargs = dict(
        name=name,
        runtime_version=runtime_version,
        api_token=api_token,
    )

    # An embedded EDM doesn't accept the `--config` argument.
    if not edm_is_embedded():
        kwargs.update(dict(edm_config=edm_config))
    return PythonEnvironment(**kwargs)


# From ci-tools ###############################################################

def _remove_readonly(func, path, _):
    """ Clear the readonly bit and reattempt the removal """
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _get_projects_to_build(exclude_self=True):
    """ Return a list of the projects to build, excluding the
    self-referential project by default.
    """
    from ci.utils.dependencies import (
        parse_source_dependencies,
        SELF_REFERENCE_ENTRY
    )

    source_deps = parse_source_dependencies(cfg.SOURCE_BUILD_FILE)

    if SELF_REFERENCE_ENTRY in source_deps and exclude_self:
        del source_deps[SELF_REFERENCE_ENTRY]

    return sorted(set(source_deps.keys()) & set(cfg.SOURCE_BUILDS_INCLUDED))


def _clone_from_github(
        dest_dir, commit_or_tag, project_name, repository, organization,
        remove_existing=True):
    """
    Get source from GitHub.

    Parameters
    ----------
    dest_dir : string
        Path of directory to clone to (excluding the name of the repository).
    commit_or_tag : string
        Branch, commit or tag to clone.
    project_name : string
        Name of the project.
    repository : string
        Name of the repository.
    organization : string
        Name of the organization.

    Returns
    -------
    module_path : string
        The path to the newly cloned repository.
    """
    project_dir = os.path.join(
        dest_dir, repository if project_name is None else project_name)

    github_token = os.environ['GITHUB_OAUTH_TOKEN']

    repo_url = "https://{token}:x-oauth-basic@github.com/{org}/{repo}".format(
        token=github_token,
        org=organization,
        repo=repository,
    )

    if remove_existing and os.path.exists(project_dir):
        shutil.rmtree(project_dir, onerror=_remove_readonly)

    cmd = [
        cfg.GIT, 'clone',
        # Override the global config setting if necessary to make sure we don't
        # accidentally modify binary files that haven't been declared as such
        # by the upstream repo. This applies particularly to a pickle file used
        # in Mayavi 4.4.4.
        '--config', 'core.autocrlf=false',
        repo_url, project_dir,
    ]
    print("Cloning {} with {}".format(project_name, cmd))
    subprocess.check_call(cmd)

    cmd = [
        cfg.GIT,
        '--work-tree', project_dir,
        '--git-dir', os.path.join(project_dir, '.git'),
        'checkout', '--detach', commit_or_tag,
    ]
    print("Getting revision {} with {}".format(commit_or_tag, cmd))
    subprocess.check_call(cmd)

    return project_dir


# Support for bundle-generation ###############################################


@contextlib.contextmanager
def _temporary_edm_environment(name, runtime_version):
    """
    Context manager to create a temporary EDM environment.  The environment is
    removed on leaving the corresponding with block.

    If the environment already exists, it will be removed first.

    Parameters
    ----------
    name : string
        Name of the environment to be created.
    runtime_version : string
        Python runtime version. (e.g., "2.7.13")

    Yields
    ------
    pyenv : PythonEnvironment
        The created environment object.
    """
    pyenv = _get_python_environment(
        name, runtime_version,
        edm_config=cfg.EDM_BUNDLEGEN_CONFIGURATION,
    )
    if pyenv.exists():
        pyenv.destroy()

    pyenv.create()
    try:
        yield pyenv
    finally:
        pyenv.destroy()


@contextlib.contextmanager
def _bundle_generation_environment():
    """
    Create a temporary EDM environment with EDM and its dependencies
    installed (via pip). This environment is needed for running the
    deploy/generate_dependencies.py script.

    Yields
    ------
    pyenv : PythonEnvironment
        The created environment object.
    """
    with _temporary_edm_environment("bundle-generation", "3.6.0") as pyenv:
        pyenv.edm([
            'install',
            '-e', pyenv.environment_name,
            '-y',
            'edm',
            'hatcher < 0.11.0'  # See: enthought/buildsystem#1524,
                                #      enthought/edm#1725
        ])
        yield pyenv


if __name__ == '__main__':
    cli()
