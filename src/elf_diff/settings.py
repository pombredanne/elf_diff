# -*- coding: utf-8 -*-

# -*- mode: python -*-
#
# elf_diff
#
# Copyright (C) 2019  Noseglasses (shinynoseglasses@gmail.com)
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with along with
# this program. If not, see <http://www.gnu.org/licenses/>.
#

from elf_diff.binary_pair_settings import BinaryPairSettings
from elf_diff.error_handling import warning

import sys
import os
import shutil
import argparse
import yaml
import datetime
from typing import Optional, Union, List, Dict, Any


class Parameter(object):
    def __init__(
        self,
        name: str,
        description: str,
        default: Optional[Union[int, float, str]] = None,
        deprecated_alias: Optional[str] = None,
        alias: Optional[str] = None,
        no_cmd_line: bool = False,
        is_flag: bool = False,
        action: Optional[str] = None,
    ):
        """Initialize parameter class."""
        self.name = name
        self.description = description
        self.default = default
        self.alias = alias
        self.deprecated_alias = deprecated_alias
        self.no_cmd_line = no_cmd_line
        self.is_flag = is_flag
        self.action = action


GROUPED_PARAMETERS: Dict[str, List[Parameter]] = {
    "Binaries": [
        Parameter("old_binary_filename", "The old version of the elf binary."),
        Parameter("new_binary_filename", "The new version of the elf binary."),
        Parameter(
            "language",
            "A hint about the language that the elf was compiled from (choices: c++).",
            default="c++",
        ),
        Parameter(
            "source_prefix",
            "A path prefix to remove from old and new source files (overridden by [old|new]_source_prefix)",
        ),
        Parameter("old_source_prefix", "A path prefix to remove from old source files"),
        Parameter("new_source_prefix", "A path prefix to remove from new source files"),
    ],
    "Report Content": [
        Parameter("project_title", "A project title to use for all reports."),
        Parameter(
            "old_alias",
            "An alias string that is supposed to be used to reference the old binary version.",
        ),
        Parameter(
            "new_alias",
            "An alias string that is supposed to be used to reference the new binary version.",
        ),
        Parameter(
            "old_info_file",
            "A text file that contains information about the old binary version.",
        ),
        Parameter(
            "new_info_file",
            "A text file that contains information about the new binary version.",
        ),
        Parameter(
            "build_info",
            "A string that contains build information that is to be added to the report.",
            default="",
        ),
        Parameter(
            "similarity_threshold",
            "A threshold value between 0 and 1 above which two compared symbols are considered being similar",
            default=0.5,
        ),
        Parameter(
            "skip_symbol_similarities",
            "If this flag is provided, symbol similarities (which are quite expensive to determine) are skipped",
            default=False,
            is_flag=True,
        ),
        Parameter(
            "consider_equal_sized_identical",
            "If this flag is defined, symbols of equal size are considered as identical (and thus ignored in most cases).",
            default=False,
            is_flag=True,
        ),
        Parameter(
            "skip_details",
            "If this flag is defined, report details are displayed",
            default=False,
            is_flag=True,
        ),
        Parameter(
            "html_template_dir",
            "A directory that contains template html files. Defaults to elf_diff's own html directory.",
            no_cmd_line=True,
        ),
    ],
    "Binutils": [
        Parameter(
            "bin_dir",
            "A place where the binutils live.",
            default=None,
        ),
        Parameter(
            "bin_prefix",
            "A prefix that is added to binutils executables.",
            default="",
        ),
        Parameter(
            "objdump_command", "Full path to the objdump untility.", default=None
        ),
        Parameter("nm_command", "Full path to the nm untility.", default=None),
        Parameter(
            "readelf_command", "Full path to the readelf untility.", default=None
        ),
        Parameter("size_command", "Full path to the size untility.", default=None),
    ],
    "Mangling": [
        Parameter(
            "old_mangling_file",
            "Full path to a mangling file for old elf.",
            default=None,
        ),
        Parameter(
            "new_mangling_file",
            "Full path to a mangling file for new elf.",
            default=None,
        ),
    ],
    "Output": [
        Parameter(
            "html_file", "The filename of the generated single page HTML report."
        ),
        Parameter("html_dir", "The directory of the generated multi page HTML report."),
        Parameter("pdf_file", "The filename of the generated PDF report."),
        Parameter("yaml_file", "The filename of the generated YAML report."),
        Parameter("json_file", "The filename of the generated JSON report."),
        Parameter("txt_file", "The filename of the generated text based report."),
        Parameter("xml_file", "The filename of the generated XML report."),
        Parameter(
            "dump_document_structure",
            "If this flag is provided, the elf_diff document structure is written to stdout",
            default=False,
            is_flag=True,
        ),
        Parameter(
            "mass_report",
            "Forces a mass report being generated. Otherwise the decision whether to generate a mass report is based on the binary_pairs found in the driver file.",
            default=False,
            is_flag=True,
        ),
    ],
    "Symbol Selection": [
        Parameter(
            "symbol_selection_regex",
            "A regex that is applied to select symbols to be considered for both, the old and the new elf file",
            default=None,
        ),
        Parameter(
            "symbol_selection_regex_old",
            "A regex that is applied to select symbols to be considered for the old elf file",
            default=None,
        ),
        Parameter(
            "symbol_selection_regex_new",
            "A regex that is applied to select symbols to be considered for the new elf file",
            default=None,
        ),
        Parameter(
            "symbol_exclusion_regex",
            "A regex that is applied to select symbols to be excluded for both, the old and the new elf file",
            default=None,
        ),
        Parameter(
            "symbol_exclusion_regex_old",
            "A regex that is applied to select symbols to be excluded for the old elf file",
            default=None,
        ),
        Parameter(
            "symbol_exclusion_regex_new",
            "A regex that is applied to select symbols to be excluded for the new elf file",
            default=None,
        ),
    ],
    "Plugins": [
        Parameter(
            "load_plugin",
            'Loads and parametrizes a plugin. Example: --load_plugin "some/path/to/module.py;PluginClass;foo1=bar2;foo2=bar2"',
            action="append",
        ),
        Parameter(
            "load_default_plugin",
            'Loads and parametrizes a default plugin. Example --load_default_plugin "html_export;single_page=False;template_dir=some_directory"',
            action="append",
        ),
        Parameter(
            "list_default_plugins",
            "Writes a list of default plugins to stdout",
            default=False,
            is_flag=True,
        ),
    ],
    "Driver Files": [
        Parameter(
            "driver_file",
            "A yaml file that contains settings and driver information.",
        ),
        Parameter(
            "driver_template_file",
            "A yaml file that is generated at the end of the run. It contains default parameters if no report was generated or, otherwise, the parameters that were read.",
        ),
    ],
}


UNGROUPED_PARAMETERS = [
    Parameter(
        "debug",
        "If enabled, elf_diff runs in debugging mode and outputs extended information if something goes wrong.",
        default=False,
        is_flag=True,
    ),
]

PARAMETERS: List[Parameter] = []
for key, value in GROUPED_PARAMETERS.items():
    PARAMETERS += value

for parameter in UNGROUPED_PARAMETERS:
    PARAMETERS.append(parameter)


class Settings(object):
    def __init__(self, module_path):
        """Initialize settings class."""
        self.module_path: str = module_path

        # To enable static type checking, we have to pre-define all command line parameters
        self.old_binary_filename: str
        self.new_binary_filename: str
        self.old_alias: str
        self.new_alias: str
        self.old_info_file: str
        self.new_info_file: str
        self.build_info: str
        self.bin_dir: str
        self.bin_prefix: str
        self.objdump_command: str
        self.nm_command: str
        self.readelf_command: str
        self.size_command: str
        self.old_mangling_file: str
        self.new_mangling_file: str
        self.html_file: str
        self.html_dir: str
        self.pdf_file: str
        self.yaml_file: str
        self.json_file: str
        self.txt_file: str
        self.xml_file: str
        self.project_title: str
        self.driver_file: str
        self.driver_template_file: str
        self.html_template_dir: str
        self.dump_document_structure: bool
        self.mass_report: bool
        self.language: str
        self.similarity_threshold: float
        self.skip_symbol_similarities: bool
        self.consider_equal_sized_identical: bool
        self.skip_details: bool
        self.symbol_selection_regex: str
        self.symbol_selection_regex_old: str
        self.symbol_selection_regex_new: str
        self.symbol_exclusion_regex: str
        self.symbol_exclusion_regex_old: str
        self.symbol_exclusion_regex_new: str
        self.load_plugin: str
        self.load_default_plugin: str
        self.list_default_plugins: bool
        self.debug: bool

        self._presetDefaults()

        cmd_line_args = Settings._parseCommandLineArgs()

        self.old_binary_filename: Optional[str] = None
        self.new_binary_filename: Optional[str] = None

        self.old_alias: Optional[str] = None
        self.new_alias: Optional[str] = None

        if cmd_line_args.driver_file:
            self.driver_file: str = cmd_line_args.driver_file
            self._readDriverFile()

        self._considerCommandLineArgs(cmd_line_args)

        self._validateAndInitSettings()

    def _presetDefaults(self) -> None:
        """Preset default values"""
        self.mass_report_members: List[BinaryPairSettings] = []

        for parameter in PARAMETERS:
            setattr(self, parameter.name, parameter.default)

    @staticmethod
    def _addParameterToGroup(
        parameter: Parameter,
        args_group: Union[argparse.ArgumentParser, argparse._ArgumentGroup],
    ) -> None:
        """Adds an argument to an arguments group or directly top level to the parser (if passed as args_group)"""
        param_name: str
        if parameter.alias:
            param_name = parameter.alias
        else:
            param_name = parameter.name

        action: str
        if parameter.is_flag:
            action = "store_true"
        else:
            action = parameter.action or "store"

        args_group.add_argument(
            "--{name}".format(name=param_name),
            default=parameter.default,
            dest=parameter.name,
            action=action,
            help=parameter.description,
        )

        if parameter.deprecated_alias:
            args_group.add_argument(
                "--{name}".format(name=parameter.deprecated_alias),
                default=parameter.default,
                dest=parameter.name,
                action=action,
                help=parameter.description + " (deprecated)",
            )

    @staticmethod
    def _prepareParser() -> argparse.ArgumentParser:
        """Prepare the argsparse command line parser and add all arguments to the parser or its args groups"""
        parser = argparse.ArgumentParser(
            description="Compares elf binaries and lists differences in symbol sizes, the disassemblies, etc."
        )

        for group_name, parameters in GROUPED_PARAMETERS.items():
            args_group = parser.add_argument_group(group_name)

            for parameter in parameters:
                if parameter.no_cmd_line:
                    continue
                Settings._addParameterToGroup(parameter, args_group)

        for parameter in UNGROUPED_PARAMETERS:
            if parameter.no_cmd_line:
                continue

            Settings._addParameterToGroup(parameter, parser)

        return parser

    @staticmethod
    def _parseCommandLineArgs() -> object:
        """Parse command line arguments"""
        parser = Settings._prepareParser()

        parser.add_argument(
            "binaries",
            nargs="*",
            default=None,
            help="The binaries to be compared (this is an alternative to --old_binary_filename and --new_binary_filename)",
        )

        actual_args: List[str] = []
        for arg_pos in range(1, len(sys.argv)):
            arg: str = sys.argv[arg_pos]
            if arg == "--":
                break
            actual_args.append(arg)

        return parser.parse_args(actual_args)

    def _readDriverFile(self) -> None:
        """Read a YAML driver file"""
        my_yaml: Dict
        with open(self.driver_file, "r") as stream:
            try:
                my_yaml = yaml.load(stream, Loader=yaml.SafeLoader)
            except yaml.YAMLError as exc:
                raise Exception(exc)

        for parameter in PARAMETERS:
            if parameter.name in my_yaml.keys():
                setattr(self, parameter.name, my_yaml[parameter.name])

        # Read binary pairs

        if "binary_pairs" in my_yaml.keys():

            bin_pair_id: int = 1

            for data_set in my_yaml["binary_pairs"]:

                short_name: str = data_set.get("short_name")
                if not short_name:
                    raise Exception(
                        f"No short_name defined for binary pair {bin_pair_id}"
                    )

                old_binary: str = data_set.get("old_binary")
                if not old_binary:
                    raise Exception(
                        f"No old_binary defined for binary pair {bin_pair_id}"
                    )

                new_binary: str = data_set.get("new_binary")
                if not new_binary:
                    raise Exception(
                        f"No new_binary defined for binary pair {bin_pair_id}"
                    )

                bp = BinaryPairSettings(short_name, old_binary, new_binary)

                self.mass_report_members.append(bp)

                bin_pair_id += 1

    def _considerCommandLineArgs(self, cmd_line_args: Any) -> None:
        """Consider the supplied command line arguments"""
        for parameter in PARAMETERS:
            if parameter.no_cmd_line:
                continue

            if hasattr(cmd_line_args, parameter.name):
                value = getattr(cmd_line_args, parameter.name)

                if value != parameter.default:
                    setattr(self, parameter.name, value)

        if len(cmd_line_args.binaries) == 0:
            pass
        elif len(cmd_line_args.binaries) == 2:
            if self.old_binary_filename is not None:
                raise Exception("Old binary filename redundantly defined")
            else:
                self.old_binary_filename = cmd_line_args.binaries[0]

            if self.new_binary_filename is not None:
                raise Exception("Old binary filename redundantly defined")
            else:
                self.new_binary_filename = cmd_line_args.binaries[1]
        else:
            raise Exception("Please specify either none or two binaries")

    def _findUtilityInBinDir(
        self, name: str, exe_extensions: List[str]
    ) -> Optional[str]:
        for exe_extension in exe_extensions:
            basename: str = self.bin_prefix + name + exe_extension

            if self.bin_dir is not None:
                command = os.path.join(self.bin_dir, basename)
                if (os.path.isfile(command)) and (os.access(command, os.X_OK)):
                    return command
        return None

    def _findUtilityUsingWhich(
        self, name: str, exe_extensions: List[str]
    ) -> Optional[str]:
        for exe_extension in exe_extensions:
            basename = self.bin_prefix + name + exe_extension
            command = shutil.which(basename)
            if (
                (command is not None)
                and (os.path.isfile(command))
                and (os.access(command, os.X_OK))
            ):
                return command
        return None

    def findUtility(self, name: str) -> None:
        """Find a utility and set a attribute of this class to the path of the utility executable"""
        command_name: str = name + "_command"
        command: Optional[str] = getattr(self, command_name)
        if command is not None:
            if (os.path.isfile(command)) and (os.access(command, os.X_OK)):
                return
            warning(f"Unable to find predefined {command_name} = {command}")

        exe_extensions: List[str]
        if os.name == "nt":
            exe_extensions = [".exe", ""]
        else:
            exe_extensions = ["", ".exe"]

        command = self._findUtilityInBinDir(name, exe_extensions)

        if command is not None:
            setattr(self, command_name, command)
            return

        command = self._findUtilityUsingWhich(name, exe_extensions)

        if command is not None:
            setattr(self, command_name, command)
            return

        raise Exception(f"Unnable to find {name} command")

    def _validateBinaries(self) -> None:
        """Validate and initialize the settings"""
        if self.old_binary_filename and not os.path.isfile(self.old_binary_filename):
            raise Exception(
                "Old binary '%s' is not a file or cannot be found"
                % (self.old_binary_filename)
            )

        if self.new_binary_filename and not os.path.isfile(self.new_binary_filename):
            raise Exception(
                "New binary '%s' is not a file or cannot be found"
                % (self.new_binary_filename)
            )

    def _prepareInfoFiles(self) -> None:
        if self.old_info_file:
            if os.path.isfile(self.old_info_file):
                with open(self.old_info_file, "r") as f:
                    self.old_binary_info = f.read()
            else:
                raise Exception(
                    "Unable to find old info file '%s'" % (self.old_info_file)
                )
        else:
            self.old_binary_info = ""

        if self.new_info_file:
            if os.path.isfile(self.new_info_file):
                with open(self.new_info_file, "r") as f:
                    self.new_binary_info = f.read()
            else:
                raise Exception(
                    "Unable to find new info file '%s'" % (self.new_info_file)
                )
        else:
            self.new_binary_info = ""

    def _prepareAlias(self) -> None:
        if self.old_alias is None:
            self.old_alias = self.old_binary_filename

        if self.new_alias is None:
            self.new_alias = self.new_binary_filename

    def _validateAndInitSettings(self) -> None:
        self._validateBinaries()

        self.findUtility("objdump")
        self.findUtility("nm")
        self.findUtility("readelf")
        self.findUtility("size")

        print("Tools:")
        print(f"   objdump: {self.objdump_command}")
        print(f"   nm:      {self.nm_command}")
        print(f"   readelf:      {self.readelf_command}")
        print(f"   size:    {self.size_command}")

        self._prepareInfoFiles()
        self._prepareAlias()

    def writeParameterTemplateFile(
        self, filename: str, output_actual_values: bool = False
    ) -> None:
        """Write a template file with all existing parameters"""
        with open(filename, "w") as f:

            f.write("# This is an auto generated elf_diff driver file\n")
            f.write(
                "# Generated by elf_diff {date}\n".format(
                    date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )
            f.write("\n")

            for parameter in PARAMETERS:

                if output_actual_values:
                    value = getattr(self, parameter.name)
                    if not value:
                        value = parameter.default

                else:
                    value = parameter.default

                f.write("# {desc}\n".format(desc=parameter.description))
                f.write("#\n")
                f.write('{name}: "{value}"\n'.format(name=parameter.name, value=value))
                f.write("\n")

    def isFirmwareBinaryDefined(self) -> bool:
        """Check if any firmware binary is defined"""
        return (self.old_binary_filename is not None) or (
            self.new_binary_filename is not None
        )
