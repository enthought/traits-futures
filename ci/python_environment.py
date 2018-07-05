# (C) Copyright 2018 Enthought, Inc., Austin, TX
# All rights reserved.
#
# The code in the ci/ package is proprietary and should not be redistributed
# without explicit approval.

import os
import re
import subprocess
import sys

# Python environment ####################################################

# Minimum usable EDM version, as a tuple of integers.
MINIMUM_EDM_VERSION = 1, 6, 0


class PythonEnvironment(object):
    """ A Python Environment provisioned by edm. """

    def __init__(self, name, runtime_version, edm_platform=None,
                 edm_config=None, api_token=None):

        # Check that EDM is new enough.
        edm_version = _edm_version()
        if edm_version < MINIMUM_EDM_VERSION:
            raise RuntimeError(
                "ci-tools requires EDM version >= {minimum_version}. "
                "Found version: {edm_version}".format(
                    minimum_version='.'.join(map(str, MINIMUM_EDM_VERSION)),
                    edm_version='.'.join(map(str, edm_version)),
                )
            )

        self.environment_name = name
        self.runtime_version = runtime_version
        self.edm_config = edm_config
        self.api_token = api_token

        if edm_platform is None:
            edm_platform = current_platform()
        self.edm_platform = edm_platform

        self.git = "git"
        if sys.platform == "win32":
            entry_suffix = ".exe"
        else:
            entry_suffix = ""

        # Extract it from edm environments prefix
        self.install_root = self.get_install_dir()

        # Add an instance attribute for each command entry point
        entry_points = ("easy_install", "pip", "coverage", "flake8", "egginst",
                        "hatcher")
        for entry in entry_points:
            entry_path = os.path.join(self.scriptsdir, entry + entry_suffix)
            setattr(self, entry, entry_path)

    @property
    def bindir(self):
        if sys.platform == "win32":
            return os.path.join(self.install_root)
        else:
            return os.path.join(self.install_root, "bin")

    @property
    def scriptsdir(self):
        if sys.platform == "win32":
            return os.path.join(self.bindir, "Scripts")
        else:
            return self.bindir

    def get_install_dir(self):
        # this might be called before the environment exists.
        # we're extracting the path from the edm info call, parsing the `root
        # directory` configuration
        results = self.edm_info(capture=True)
        lines = results.split('\n')
        for line in lines:
            if 'root directory' in line:
                # Windows root directory has multiple : in the line
                _, root_directory = line.split(':', 1)
                return os.path.join(
                    root_directory.strip(), 'envs',
                    self.environment_name
                )
        else:
            raise ValueError("Can't find the install directory")

    def rungit(self, command, capture=False):
        """ Run the given command locally using git.
        """
        cmd = [self.git] + command
        if capture:
            return subprocess.check_output(cmd)
        else:
            return subprocess.check_call(cmd)

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

    def exists(self):
        """
        Return True if an EDM environment has already been created, else False.
        """
        cmd = ["environments", "exists", self.environment_name]
        return not self.edm_nocheck(cmd)

    def create(self):
        """
        Create a new Python environment.
        """
        cmd = [
            'environments', 'create', self.environment_name,
            '--version', self.runtime_version,
            '--platform', self.edm_platform,
            '--force',
        ]
        self.edm(cmd)

    def create_from_bundle(self, bundle):
        """
        Create a Python environment from a given bundle.
        """
        cmd = [
            'environments', 'import', self.environment_name,
            '--filename', bundle,
        ]
        self.edm(cmd)

    def destroy(self):
        """
        Remove an existing environment, completely.
        """
        cmd = [
            'environments', 'remove',
            '--purge', '--yes',
            self.environment_name,
        ]
        self.edm(cmd)

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
        cmd = [
            "run",
            "--environment", self.environment_name,
            "--",
        ] + command
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
            "--environment", self.environment_name,
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

    def edm_info(self, capture=False):
        """ Get EDM info.

        If *capture* is true, return the output of "edm info" as a string.
        Otherwise, print it to the console.
        """
        if capture:
            return self.edm_capture(["info"])
        else:
            self.edm(["info"])

    def edm_install(self, command, capture=False):
        """ Run edm install the configured environment.

        The '--yes' option avoids prompts that would wait for user input.
        """
        return self.run(["edm", "install", "--yes"] + command, capture)

    def runhatcher(self, command, capture=False):
        """ Run hatcher locally using this environment's python interpreter
        """
        if not os.path.exists(self.hatcher):
            raise RuntimeError("Hatcher must be installed to use runhatcher!")

        return self.run([self.hatcher] + command, capture)

    def runegginst(self, egg, capture=False):
        """ Run egginst locally using this environment's python interpreter
        """
        if not os.path.exists(self.egginst):
            raise RuntimeError("egginst must be installed to use runegginst!")

        return self.run([self.egginst, egg], capture)

    def get_pep425_python_tag(self):
        ci_tools_dir = os.path.abspath(os.path.dirname(__file__))
        script = os.path.join(ci_tools_dir, 'pep425tags.py')
        python_tag = self.python(script, capture=True)
        return python_tag.strip()

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

    @property
    def compiler_switch(self):
        return '--compiler=msvc' if 'win' in self.edm_platform else ''


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
        return "rh6-x86_64"
    elif platform == "darwin":
        return "osx-x86_64"
    else:
        raise RuntimeError("platform {!r} not supported".format(platform))


def _edm_version():
    """ Determine the EDM version.

    Returns the EDM version as a tuple of integers.
    """
    edm_version_info = subprocess.check_output(["edm", "--version"]).decode(
        "utf-8")
    m = re.match(r'(?:EDM|edm) (?P<version>\d+\.\d+\.\d+)', edm_version_info)
    version = m.group('version')
    return tuple(int(piece) for piece in version.split('.'))


def edm_is_embedded():
    """ Determine whether EDM is embedded (e.g., Canopy's EDM) or standalone.

    Returns
    -------
    is_embedded : bool
        True if EDM is embedded, else False.

    Raises
    ------
    RuntimeError
        If unable to interpret the output of "edm info".
    """
    edm_info = subprocess.check_output(["edm", "info"]).decode("utf-8")
    match = re.search(
        r"^running mode:\s*\b(?P<mode>.*)\b\s*$",
        edm_info, re.MULTILINE)
    if match is None:
        raise RuntimeError(
            "Unable to determine EDM running mode. No line starting with "
            "'running mode:' in the output of 'edm info'")

    mode = match.group('mode')
    if mode == "embedded":
        return True
    elif mode == "standalone":
        return False
    else:
        raise RuntimeError(
            "Don't know how to interpret running mode: {!r}".format(mode))
