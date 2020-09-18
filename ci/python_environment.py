# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

import os
import re
import subprocess
import sys

# Python environment ####################################################

# Minimum usable EDM version, as a tuple of integers.
MINIMUM_EDM_VERSION = 1, 6, 0


class PythonEnvironment:
    """ A Python Environment provisioned by edm. """

    def __init__(
        self,
        name,
        runtime_version,
        edm_platform=None,
        edm_config=None,
        api_token=None,
    ):

        # Check that EDM is new enough.
        edm_version = _edm_version()
        if edm_version < MINIMUM_EDM_VERSION:
            raise RuntimeError(
                "ci-tools requires EDM version >= {minimum_version}. "
                "Found version: {edm_version}".format(
                    minimum_version=".".join(map(str, MINIMUM_EDM_VERSION)),
                    edm_version=".".join(map(str, edm_version)),
                )
            )

        self.environment_name = name
        self.runtime_version = runtime_version
        self.edm_config = os.path.abspath(edm_config)
        self.api_token = api_token

        if edm_platform is None:
            edm_platform = current_platform()
        self.edm_platform = edm_platform

    def edm(self, command):
        """
        Run an EDM command, with configuration taken from this
        environment.

        Parameters
        ----------
        command : list of string
            The tail part of the edm command.

        Raises
        ------
        subprocess.CalledProcessError
            If the edm command returns a nonzero return code.
        """
        return subprocess.check_call(self._edm_base_command + command)

    def edm_nocheck(self, command):
        """
        Run an EDM command, with configuration taken from this
        environment. Don't fail on error, but return the subprocess return
        code.

        Parameters
        ----------
        command : list of string
            The tail part of the edm command.

        Returns
        -------
        returncode : int
            The return code from the subprocess call.
        """
        return subprocess.call(self._edm_base_command + command)

    def edm_capture(self, command):
        """
        Run an EDM command, with configuration taken from this
        environment. Capture any output to stdout and return it.

        Parameters
        ----------
        command : list of string
            The tail part of the edm command.

        Returns
        -------
        output : string
            The captured output from the edm command.

        Raises
        ------
        subprocess.CalledProcessError
            If the edm command returns a nonzero return code.
        """
        output = subprocess.check_output(self._edm_base_command + command)
        return output.decode("utf-8")

    def create(self, force=True, bare=True):
        """
        Create a new Python environment.

        Parameters
        ----------
        force : bool
            If True (the default), remove any environment with the
            same name. If False, and there's an existing directory
            matching the name of the environment, this command
            will fail.
        bare : bool
            If True (the default), don't install any packages at all
            into the new environment. If False, standard packages
            like setuptools and pip get installed.
        """
        cmd = [
            "environments",
            "create",
            self.environment_name,
            "--version",
            self.runtime_version,
            "--platform",
            self.edm_platform,
        ]
        if force:
            cmd.append("--force")
        if bare:
            cmd.append("--bare")

        self.edm(cmd)

    def destroy(self):
        """
        Remove an existing environment, completely.
        """
        cmd = [
            "environments",
            "remove",
            "--purge",
            "--yes",
            self.environment_name,
        ]
        self.edm(cmd)

    def exists(self):
        """
        Return True if an EDM environment has already been created, else False.
        """
        cmd = ["environments", "exists", self.environment_name]
        return not self.edm_nocheck(cmd)

    def install(self, requirements):
        """
        Install requirements into the environment.
        """
        install_cmd = [
            "install",
            "--environment",
            self.environment_name,
            "--yes",
        ]
        install_cmd.extend(requirements)

        self.edm(install_cmd)

    def run(self, command, capture=False):
        """
        Run the given command with this environment's shell.

        Raise on nonzero return code. See the ``python_return_code`` method for
        a variant that captures and returns the error code.

        Parameters
        ----------
        command : list
            List of arguments to be passed to Python.
        capture : bool
            Flag to return process stdout or return code

        Returns
        -------
        The return code of the subprocess or its stdout
        depending on the capture flag.
        """
        cmd = ["run", "--environment", self.environment_name, "--"] + command
        if capture:
            return self.edm_capture(cmd)
        else:
            return self.edm(cmd)

    def python_return_code(self, command):
        """
        Run the given command with this environment's Python interpreter,
        and return the process return code.

        Parameters
        ----------
        command : list
            List of arguments to be passed to Python.

        Returns
        -------
        The return code of the subprocess.

        The script is run within the activated environment.
        """
        cmd = [
            "run",
            "--environment",
            self.environment_name,
            "--",
            "python",
        ] + command
        return self.edm_nocheck(cmd)

    def python(self, command, capture=False):
        """
        Run the given command with this environment's Python interpreter,

        Raise on nonzero return code. See the ``python_return_code`` method for
        a variant that captures and returns the error code.

        Parameters
        ----------
        command : list
            List of arguments to be passed to Python.
        capture : bool
            Flag to return process stdout or return code

        Returns
        -------
        The return code of the subprocess or its stdout
        depending on the capture flag.

        The script is run within the activated environment.
        """
        return self.run(["python"] + command, capture)

    @property
    def _edm_base_command(self):
        """
        Base command for invoking EDM, specifying the appropriate config
        file and token.
        """
        cmd = ["edm"]
        if self.edm_config is not None:
            cmd.extend(["--config", self.edm_config])
        if self.api_token is not None:
            cmd.extend(["--api-token", self.api_token])
        return cmd


# Utils ################################################################


def current_platform():
    """
    Return a string representing the current platform, in the format
    accepted by EDM.
    """
    is_64bits = sys.maxsize > 2 ** 32
    platform = sys.platform
    if platform.startswith("win32"):
        return "win-x86_64" if is_64bits else "win-x86"
    elif platform.startswith("linux"):
        return "rh7-x86_64"
    elif platform == "darwin":
        return "osx-x86_64"
    else:
        raise RuntimeError("platform {!r} not supported".format(platform))


def _edm_version():
    """ Determine the EDM version.

    Returns the EDM version as a tuple of integers.
    """
    edm_version_info = subprocess.check_output(["edm", "--version"]).decode(
        "utf-8"
    )
    m = re.match(r"(?:EDM|edm) (?P<version>\d+\.\d+\.\d+)", edm_version_info)
    version = m.group("version")
    return tuple(int(piece) for piece in version.split("."))
