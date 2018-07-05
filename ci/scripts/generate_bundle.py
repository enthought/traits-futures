# (C) Copyright 2018 Enthought, Inc., Austin, TX
# All rights reserved.
#
# The code in the ci/ package is proprietary and should not be redistributed
# without explicit approval.

"""
Script to generate a bundle from a list of dependencies, on any
target platform (not necessarily the same as the platform
that the script is being executed on).

Example usage
=============
To generate a bundle file for Sphinx and its dependencies, for 64-bit Windows:

    $ python generate_bundle.py --platform win-x86_64 sphinx -f bundle.json

This script must be run under a Python environment that includes EDM
and its dependencies (including in particular the "click" library,
which we use for argument parsing). Here's one way of setting up
such an environment:

    git clone --branch v1.8.2 git@github.com:enthought/edm.git
    edm envs create deps-analysis
    edm run -e deps-analysis -- pip install ./edm

"""
import itertools
import json
import operator

import click
import six

from edm.api import Session
from edm.cli.click_custom import (
    convert_string_to_epd_platform,
    convert_string_to_runtime_implementation,
)
from edm.cli.common import (
    allow_newer_older_any,
    RUNTIME_IMPLEMENTATION_HELP,
    RUNTIME_VERSION_HELP,
)
from edm.cli.context import EdmContext
from edm.cli.utils import ensure_settings
from edm.constants import (
    DEFAULT_IMPLEMENTATION,
    Implementation,
    IMPLEMENTATION_TO_DEFAULT_VERSION,
    UNSET
)
from edm.core._sat_solver import SATSolver
from edm.core.bundle.models import (
    ConstraintModifiersV1,
    EnvironmentBundleV1,
    EnvironmentBundleV2,
    MarkV1,
    RequirementV1,
    RequirementV2,
    RuntimeMetadataV1,
    RuntimeMetadataV2,
)
from edm.core.environments_manager import _fetch_bundle_assets
from edm.core.modifiers_database import ModifiersDatabase
from edm.core.packages_mark import PackagesMarkDatabase
from edm.core.packages_repository import _convert_requirements
from edm.core.repository_utils import (
    packages_repositories_factory,
    PackagesRepository,
    runtimes_repositories_factory,
    RuntimesRepository,
)
from edm.default_platform import DEFAULT_EPD_PLATFORM
from edm.network import AssetFetcher
from okonomiyaki.runtimes.runtime_info import IRuntimeInfo
from okonomiyaki.runtimes.runtime_metadata import runtime_metadata_factory
from okonomiyaki.versions import MetadataVersion
from simplesat import Request
from simplesat.constraints import ConstraintModifiers

# Concatenate a list of lists (or iterable of iterables) to a single iterable.
concatenate = itertools.chain.from_iterable


def solver_factory(settings, platform, python_tag):
    """
    Create SATSolver instance for the given settings, platform
    and Python version.
    """
    with Session.authenticated_from_settings(settings) as session:
        asset_fetcher = AssetFetcher.from_settings(session, settings)
        repository_names = tuple(
            repository.full_name for repository in settings.repositories)
        packages_repositories, _ = packages_repositories_factory(
            asset_fetcher,
            repository_names,
            platform,
            python_tag,
            settings.publisher,
        )
        installed_repository = PackagesRepository()

    return SATSolver.from_enstaller_repositories(
        packages_repositories, installed_repository)


def get_runtime_info(settings, platform, implementation, version):
    with Session.authenticated_from_settings(settings) as session:
        asset_fetcher = AssetFetcher.from_settings(session, settings)
        repository_names = [r.full_name for r in settings.runtime_repositories]
        runtimes_repositories, _ = runtimes_repositories_factory(
            asset_fetcher, repository_names, platform, settings.publisher)

        runtimes_repository = RuntimesRepository()
        for repository in runtimes_repositories:
            runtimes_repository.update(repository)

        latest = runtimes_repository.latest_for_implementation(
            implementation.name, version)

        # We only need the runtime metadata, not the runtime itself.
        # Unfortunately, those metadata are embedded in the runtime
        # zip file, so we need to fetch the entire file.
        target = asset_fetcher.fetch_runtime(latest)
        return latest, runtime_metadata_factory(target)


def create_marks_db(requirements, packages):
    """
    Create a marks database for the given manual requirements
    and computed packages.
    """
    # Mark dependencies as auto, specified packages as manual.
    marks_db = PackagesMarkDatabase(mutable=True)
    for package in packages:
        marks_db.mark_package_auto(package.name, override=False)
    for requirement in requirements:
        marks_db.mark_package_manual(requirement.name, override=True)
    return marks_db


def resolve_requirements(
        requirements, modifiers, settings, platform, python_tag):
    """
    Solve a set of package requirements.

    Parameters
    ----------
    requirements : list of simplesat.constraints.requirement.Requirement
        List of core requirements.
    modifiers : simplesat.constraints.constraint_modifiers.ConstraintModifiers
        Constraint modifiers, e.g., allow-newer, allow-older, etc.
    settings : edm.settings.core.Settings
        The EDM settings (token, configuration, repositories, etc.)
    platform : okonomiyaki.platforms.epd_platform.EPDPlatform
        The platform to do the resolution for.
    python_tag : unicode string
        E.g., "cp27", "pp36", following PEP 425.

    Returns
    -------
    packages : list of edm.core.package_metadata.RemotePackageMetadata
        Explicit list of computed packages, sorted by name.
    """
    # Perform the package resolution.
    request = Request(modifiers=modifiers)
    for requirement in requirements:
        request.install(requirement)

    solver = solver_factory(settings, platform, python_tag)
    actions, _ = solver.resolve(request)

    packages = [package for opcode, package in actions if opcode == "install"]
    return sorted(packages, key=operator.attrgetter("name"))


def generate_bundle(
        requirements,
        allow_newer=[], allow_older=[], allow_any=[],
        config=None, api_token=None,
        version=None,
        implementation=None,
        platform=None,
        bundle_format="1.0"):
    """
    Generate bundle from requirements, for a given platform.

    Parameters
    ----------
    requirements : iterable of string
        EDM requirements as strings.
    allow_newer : iterable of string, optional
        Package names for which we allow a newer version to override the
        constraints arising from dependencies.
    allow_older : iterable of string, optional
        Package names for which we allow an older version to override the
        constraints arising from dependencies.
    allow_any : iterable ot string, optional
        Package names for which we allow any version to override the
        constraints arising from dependencies.
    config : str, optional
        Path to EDM configuration file. If not specified, the EDM global
        configuration file is used.
    api_token : str, optional
        Token for API access, if required. If no token is given, only the free
        repositories will be available.
    version : str, optional
        Version specifier (possibly partial), for example "2.7".
    implementation : Implementation
        Implementation: for example, cpython, pypy, julia. The default is
        Implementation.cpython.
    platform : EPDPlatform, optional
        Platform to do the dependency generation for. If not specified, the
        default value for this platform will be used.
    bundle_format : str, optional
        Metadata format for the bundle. Either "1.0" (the default)
        or "2.0".

    Returns
    -------
    bundle : EnvironmentBundleV1
        The generated bundle.
    """
    if implementation is None:
        implementation = DEFAULT_IMPLEMENTATION
    if version is None:
        version = IMPLEMENTATION_TO_DEFAULT_VERSION[implementation]

    if platform is None:
        platform = DEFAULT_EPD_PLATFORM

    # Get the appropriate settings from api token and EDM configuration.
    context = EdmContext(config or UNSET, api_token or UNSET)
    settings = ensure_settings(context)

    bundle_format = MetadataVersion.from_string(bundle_format)

    # Get the python tag and other metadata.
    runtime_info, runtime_metadata = get_runtime_info(
        settings, platform, implementation, version)
    python_tag = runtime_metadata.python_tag

    # Convert requirement strings to Requirement objects.
    requirements = _convert_requirements(requirements)

    # Perform the package resolution.
    constraint_modifiers = ConstraintModifiers(
        allow_newer=allow_newer,
        allow_older=allow_older,
        allow_any=allow_any,
    )

    packages = resolve_requirements(
        requirements, constraint_modifiers, settings, platform, python_tag)

    repository_names = tuple(
        six.text_type(repository.full_name)
        for repository in settings.repositories
    )
    runtime_repository_names = tuple(
        six.text_type(repository.full_name)
        for repository in settings.runtime_repositories
    )

    marks_db = create_marks_db(requirements, packages)
    marks = tuple(MarkV1(**item) for item in marks_db.to_json())

    modifiers_db = ModifiersDatabase(constraint_modifiers)
    modifiers = ConstraintModifiersV1(**modifiers_db.to_json_dict())
    environment = IRuntimeInfo.factory_from_metadata(
        runtime_metadata, u"dummy", u"dummy")

    if bundle_format == MetadataVersion(1, 0):
        return EnvironmentBundleV1(
            repository_names,
            runtime_repository_names,
            RuntimeMetadataV1(
                environment.implementation,
                platform,
                environment.abi,
                environment.version,
            ),
            tuple(
                RequirementV1(
                    package.name,
                    package.version,
                )
                for package in packages
            ),
            modifiers,
            marks,
        )

    elif bundle_format == MetadataVersion(2, 0):
        return EnvironmentBundleV2(
            repository_names,
            runtime_repository_names,
            RuntimeMetadataV2(
                environment.implementation,
                platform,
                environment.abi,
                environment.version,
                six.text_type(runtime_info.repository_info.full_name),
                runtime_info.sha256,
            ),
            tuple(
                RequirementV2(
                    package.name,
                    package.full_version,
                    six.text_type(package.repository_info.full_name),
                    package.sha256,
                )
                for package in packages
            ),
            modifiers,
            marks,
        )

    else:
        raise ValueError(
            "Unsupported bundle format: {!r}".format(bundle_format)
        )


@click.command()
@click.option(
    "-c", "--config",
    help="Path to EDM configuration file",
    type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-t", "--api-token", help="API token", envvar="EDM_API_TOKEN")
@click.option(
    "-f", "--output-file",
    type=click.File("w"),
    help="Write bundle to the given file.",
)
@click.option(
    "-m", "--bundle-format",
    type=click.Choice(["1.0", "2.0"]),
    default="1.0",
    help="Bundle format",
)
@click.option(
    "-i", "--include-assets",
    default=False, is_flag=True,
    help="If given, will create a data bundle. Implies \n"
         "--bundle-format 2.0",
)
@click.option(
    "--version",
    default=None,
    help=RUNTIME_VERSION_HELP,
)
@click.option(
    "--implementation",
    default=Implementation.cpython.name,
    type=click.Choice([interpreter.name for interpreter in Implementation]),
    callback=convert_string_to_runtime_implementation,
    help=RUNTIME_IMPLEMENTATION_HELP
)
@click.option(
    "--arch", "--platform",
    callback=convert_string_to_epd_platform,
    help=(
        "Specify a runtime platform (e.g. \"rh6-x86_64\", "
        "\"win-x86_64\", etc...). See `edm help platforms` for details."
    ),
)
@click.argument("requirements", nargs=-1)
@allow_newer_older_any
def main(version, implementation, platform, requirements,
         config, api_token, bundle_format, include_assets,
         allow_newer, allow_older, allow_any,
         output_file):
    """
    Create bundle from requirements.
    """

    if include_assets:
        bundle_format = '2.0'

    bundle = generate_bundle(
        config=config,
        api_token=api_token,
        version=version,
        implementation=implementation,
        platform=platform,
        requirements=requirements,
        bundle_format=bundle_format,
        # allow_newer and friends arrive as a tuple of tuples
        allow_newer=concatenate(allow_newer),
        allow_older=concatenate(allow_older),
        allow_any=concatenate(allow_any),
    )

    if include_assets:
        # Get the appropriate settings from api token and EDM configuration.
        context = EdmContext(config or UNSET, api_token or UNSET)
        settings = ensure_settings(context)
        with Session.authenticated_from_settings(settings) as session:
            asset_fetcher = AssetFetcher.from_settings(session, settings)
            runtime_path, package_paths = _fetch_bundle_assets(
                bundle, settings, asset_fetcher
            )
            bundle.write_as_data_bundle(
                output_file.name, runtime_path, package_paths,
                settings.publisher
            )

    else:
        bundle_as_json_object = bundle.to_json_dict()
        # Workaround for enthought/edm#1721.
        bundle_as_json_object["modifiers"]["allow_any"].sort()
        bundle_as_json_object["modifiers"]["allow_newer"].sort()
        bundle_as_json_object["modifiers"]["allow_older"].sort()
        environment_data = json.dumps(
            bundle_as_json_object, indent=4, separators=(",", ": "),
            sort_keys=True,
        )

        click.echo(environment_data, file=output_file)


if __name__ == "__main__":
    main()
