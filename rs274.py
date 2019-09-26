#!/usr/bin/env python3
"""RS274 implements an RS274 parser for CNC pre/post-processors."""
# <---------------------------------------- 100 characters --------------------------------------> #
# FreeCad Path documentation:
# https://www.freecadweb.org/wiki/Path_scripting

# Tasks:
# * Add test suite for groups.
# * Add test suite for block parsing.
# * Add sticky variables, types, and units.
# * Improve *Group* construction documentation.
# * Add G2/G3 R => IJK conversion.
# * Add units conversion.
# * Allow for multiple modal groups rather than just the motion group?
# * Add re-blocker code.
# * Add routine call type checking using type hinting.
# * Improve Error/Waring messages.
#
# Documentation, Linting:
# * Add type annotation via PEP484, PEP3107.
# * https://aboutsimon.com/blog/2018/04/04/
#      Python3-Type-Checking-And-Data-Validation-With-Type-Hints.html
# * https://medium.com/@ageitgey/
#      learn-how-to-use-static-type-checking-in-python-3-6-in-10-minutes-12c86d72677b
# * http://google.github.io/styleguide/pyguide.html
# * https://realpython.com/python-virtual-environments-a-primer/

import argparse
import math
import os
from io import IOBase

# Import some types for type hints:
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
Number = Union[float, int]
Error = str


def main():
    """Command line program for processing CNC files in rs274 format."""
    # Set up a command line *parser*;
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="RS274 post processor.")

    parser.add_argument("cnc_files", metavar=".cnc", type=str, nargs="+",
                        help="A .cnc file to process.")
    parser.add_argument("-v", "--verbose", action="count",
                        help="Increase tracing level (defaults to 0 which is off)")
    parsed_arguments: Dict[str, Any] = vars(parser.parse_args())

    # Create and initialize *rs274*:
    rs274: RS274 = RS274()
    rs274.groups_create()
    rs274.token_match_tests()

    # Process the *cnc_file_names*:
    verbose_count: int = parsed_arguments["verbose"]
    cnc_file_names = parsed_arguments["cnc_files"]
    for index, cnc_file_name in enumerate(cnc_file_names):
        print(f"[index]'{cnc_file_name}'")
        cnc_file: IOBase
        with open(cnc_file_name, "r") as cnc_file:
            content: str = cnc_file.read()
            commands: List[Command] = rs274.content_parse(content, trace=bool(verbose_count))
            commands = RS274.n_remove(commands)
            commands = RS274.g28_remove(commands)
            commands = RS274.g91_remove(commands)
            commands = RS274.drill_cycles_replace(commands)
            rs274.commands_write(commands, os.path.join("/tmp", cnc_file_name))
            # commands = rs274.g83.replace(commands)
            # for command_index, command in enumerate(commands):
            #        print(" Commandx[{0}]: {1}".format(command_index, command))


# Command:
class Command:
    """Alternative Command class implementation.

    This is an alternative implementation of the the Command class
    for FreeCAD for use when the rs274 module is being used outside
    of FreeCAD.  This class typically represents a single executable
    G/M code with parameters.  It can also represent comments.
    """

    # Command.__init__():
    def __init__(self, name: str, parameters: Optional[Dict[str, Number]] = None):
        """Initialize a *Command* with a name and optional parameters.

        Arguments:
            name (str): The name of the command (e.g. "G0", "M3", etc.)
                A comment is entered as "( comment text )" for the name.
            parameters (dict):  A dictionary that contains the paramter
                values.  Example: "G0 X1.2 Y3.4" would have a parameter
                dictionary of {'X':1.2, 'Y':3.4}.

        """
        # Create an empty *parameters* dictionary if needed:
        if parameters is None:
            parameters = dict()

        # Stuff arguments into *command* (i.e. *self*):
        command: Command = self
        self.Name: str = name
        self.Parameters: Dict[str, Number] = dict() if parameters is None else parameters
        command = command

    # Command.__str__():
    def __str__(self) -> str:
        """Return a string reprentation of a *Command*."""
        # Grab some values from *command* (i.e. *self*):
        command: Command = self
        name: str = command.Name
        parameters: Dict[str, Number] = command.Parameters

        # Create a sorted list of *parameters_strings*:
        parameters_strings: List[str] = list()
        letter: str
        number: Number
        for letter, number in parameters.items():
            parameters_strings.append(f"{letter}{number}")
        parameters_strings.sort()

        # Generate and return the final *result*:
        parameters_text: str = ' '.join(parameters_strings)
        result: str = f"{name} {parameters_text}" if parameters_text else f"{name}"
        return result


# Group:
class Group:
    """Represents a group of releated Template objects."""

    # Group.__init__():
    def __init__(self, rs274: "RS274", short_name: str, title: str):
        """Initialize the a Group object.

        Arguments:
            rs274 (RS274): The RS274 object that contains the master
                group tables.
            short_name (str): The short group name.  Usually the first
                 G/M code of the group (e.g. "G0", "M3", etc.)
            title (str): A descriptive title for group
                (e.g. "Motion Control")

        """
        # Stuff arguments into *group* (i.e. *self*):
        group: Group = self
        self.key: int = -1
        self.templates: Dict[str, Template] = dict()
        self.title: str = title
        self.rs274: RS274 = rs274
        self.short_name: str = short_name
        group = group

    # Group.g_code():
    def g_code(self, name: str, parameters: str, title: str):
        """Create an named G code Template with parameters and title.

        Arguments:
            name (str): The G-code name as a string of the form "G#"
                where "#" is a number.
            parameters (str): The list of parameters letters (e. g.
                "ABCXYZ".
            title (str): A short description of the G-code does.

        """
        # Create *g_code_template and register it with *group* (i.e. *self*):
        g_code_template: Template = Template(name, parameters, title)
        group: Group = self
        group.template_register(g_code_template)

    # Group.m_code():
    def m_code(self, name: str, parameters: str, title: str):
        """Create a named M code Template with parameters and title.

        Arguments:
            name (str): The M-code as a string of the form "M#"
                where "#" is a number.
            parameters (str): The list of parameter letters.
            title (str): A short description of the M-code does.

        """
        # Create *g_code_template*:
        m_code_template: Template = Template(name, parameters, title)

        # Register *m_code_template* template with *group* (i.e. *self*):
        group: Group = self
        group.template_register(m_code_template)

        # Record *group* with *groups_table*:
        rs274: RS274 = group.rs274
        groups_table: Dict[str, Group] = rs274.groups_table
        assert name in groups_table, f"name={name}"
        # print(f"m_code_template={m_code_template}")

    # Group.letter_code():
    def letter_code(self, letter: str, title: str):
        """Create a letter code Template with a title.

        Arguments:
            letter (str): The letter code letter (e.g. 'T', 'F', ...)
            title (str): A short description of the letter code does.

        """
        # Register *letter_template* with *group* (i.e. *self*):
        group: Group = self
        letter_template: Template = Template(letter, "", title)
        group.template_register(letter_template)

    # Group.template_register():
    def template_register(self, template: "Template"):
        """Register a new template with with group.

        Arguments:
            template (Template): The template to register with group.

        """
        # Grab some values from *group* (i.e. *self*) and *rs274*:
        group: Group = self
        group_templates: Dict[str, Template] = group.templates
        rs274: RS274 = group.rs274
        parameter_letters: Dict[str, Number] = rs274.parameter_letters
        templates_table: Dict[str, Template] = rs274.templates_table
        groups_table: Dict[str, Group] = rs274.groups_table

        # Make sure that *name* is not duplicated in the global *templates_table*:
        name: str = template.name
        assert name not in templates_table, f"Template '{name}' already in global templates table.'"
        templates_table[name] = template
        groups_table[name] = group

        # Load up *parameter_letters* from *parameters*:
        parameters: Dict[str, Number] = template.parameters
        parameter: str
        for parameter in parameters.keys():
            if len(parameter) == 1 and parameter.isalpha() and parameter.isupper():
                parameter_letters[parameter] = 0

        # Make sure that *template* is not duplicated in *group_templates*:
        assert name not in group_templates, (f"Template '{name}' is duplicated"
                                             f" in group '{group.short_name}'")
        group_templates[name] = template


# RS274:
class RS274:
    """Represents an RS-274 (i.e. CNC code) processor."""

    # Various types that can be applied to variable values:
    # TYPE_COUNT     = 0  # Non-negative integer
    # TYPE_DEGREES   = 1  # An angle measured in degrees
    # TYPE_FEED      = 2  # A speed measured in meter/second or inch/minute
    # TYPE_LENGTH    = 3  # A length measured either in millimeters or inches
    # TYPE_ROTATION  = 4  # A rotational speed measured in either xxx or rev./second
    # TYPE_TIME      = 5  # A time messured in seconds

    # RS274:__init__():
    def __init__(self):
        """Initialize the RS274 object."""
        # Load some values into *rs274* (i.e. *self*):
        rs274: RS274 = self
        self.comment_group: Optional[str] = None      # *Group* for comments (e.g. "( ... )")
        self.group_table: Dict[str, Group] = dict()   # Command name (e.g. "G0") for assoc. *Group*"
        self.groups_list: List[Group] = list()        # *Group*'s list in execution order
        self.groups_list_keyed: List[Group] = False   # *True* if all groups assigned a sort key
        self.groups_table: Dict[str, Group] = dict()  # *Group*'s table keyed with short name
        self.line_number_group: Optional[Group] = None  # *Group* for N codes.
        self.motion_command_name: str = ""              # Name of last motion command (or *None*)
        self.motion_group: Optional[Group] = None       # The motion *Group* is special
        self.parameter_letters: Dict[str, Number] = dict()  # For test, collect all template params.
        self.templates_table: Dict[str, Template] = dict()  # Command name (e.g. "G0") to *Template*
        self.variables: Dict[str, None] = dict()        # Unclear if this is needed....
        self.white_space: str = " \t"                   # White space characters for tokenizing
        self.token_match_routines: Tuple[Callable] = (  # The ordered token match routines
            OLetterToken.match,
            LetterToken.match,
            CommentToken.match,
            BracketToken.match
        )
        rs274 = rs274

    # RS274.assign_group_keys()
    def assign_group_keys(self):
        """Ensure that every Group has a valid key."""
        # Do nothing if *groups_list_keyed* is already set.  Any modifications to
        # the grouops of *rs274* (i.e. *self*) will reset *groups_list_keyed*:
        rs274: RS274 = self
        groups_list_keyed = rs274.groups_list_keyed
        if not groups_list_keyed:
            # Sweep through *groups_list* and set the key attribute for each *group*:
            groups_list: List[Group] = rs274.groups_list
            index: int
            group: Group
            for index, group in enumerate(groups_list):
                group.key = index

            # Remember that *groups_list_keyed*:
            rs274.groups_list_keyed = True

    # RS274:commands_and_unused_tokens_extract():
    @staticmethod
    def commands_and_unused_tokens_extract(tokens: "List[Token]",
                                           tracing: Optional[str] = None) -> Tuple[
                                               List[Command],
                                               "List[Token]"]:
        """Split tokens into commands and tokens.

        Arguments:
            tokens (List[Token]): List to tokens to process.
            tracing (Optionial[str]): None for no tracing; otherwise
                the string to prefix to tracing output.

        Returns:
            List[Command]: A list of commands extracted.
            List[Token]: A list of unused Token's.

        """
        # Perform any requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        tokens_text: str = ""
        if tracing is not None:
            tokens_text = RS274.tokens_to_text(tokens)
            print(f"{tracing}=>RS274.commands_and_unused_tokens_extract({tokens_text}, *)")

        # Sweep through *tokens* splitting them into *commands* and *unused_tokens* and
        # collecting *errors* as we go:
        commands: List[Command] = list()
        unused_tokens: List[Token] = list()
        token: Token
        for token in tokens:
            token.catagorize(commands, unused_tokens)

        # Wrap up any requested *tracing* and return both *commands* and *unused_tokens*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            tokens_text = RS274.tokens_to_text(tokens)
            commands_text: str = RS274.commands_to_text(commands)
            unused_tokens_text: str = RS274.tokens_to_text(unused_tokens)
            print(f"{tracing}<=RS274.commands_and_unused_tokens_extract({tokens_text}, *)"
                  f"=>{commands_text}, '{unused_tokens_text}'")
        return commands, unused_tokens

    # RS274.commands_to_text():
    @staticmethod
    def commands_to_text(commands: List[Command]) -> str:
        """Return Command's list as a string."""
        return '[' + "; ".join(f"{command}" for command in commands) + ']'

    # RS274.commands_from_tokens():
    def commands_from_tokens(self,
                             tokens: "List[Token]",
                             tracing: Optional[str] = None) -> Tuple[List[Command],
                                                                     List[Error],
                                                                     "List[LetterToken]",
                                                                     str]:
        """Return the commands extracted from tokens.

        Arguments:
            tokens (List[Token]): The tokens to process.
            tracing (Optionial[str]): None for no tracing; otherwise
                the string to prefix to tracing output.

        Returns:
            List[Command]: The list of Command's that were extracted.
            List[Error]: The list of Error's detected.
            List[Token]: A list of unused Token's, and
            str: The default motion command name to use afterwards.

        """
        # Define some variables to make `mypy` happy:
        unused_tokens_text: str = ""
        tokens_text: str = ""
        commands_text: str = ""

        # Perform any requested *tracing*:
        next_tracing: Optional[str] = None if tracing is None else tracing + " "
        if tracing is not None:
            tokens_text = RS274.tokens_to_text(tokens)
            print(f"{tracing}=>RS274.commands_from_tokens('{tokens_text}')")

        # First partition *tokens* into *commands* and *unused_tokens* using *rs274* (i.e. *self*).
        # Tack any *extraction_errors* onto *errors*:
        rs274: RS274 = self
        commands: List[Command]
        unused_tokens: List[Token]
        commands, unused_tokens = \
            RS274.commands_and_unused_tokens_extract(tokens, tracing=next_tracing)

        # Fill up *unused_tokens_table* with each *unused_token* appending any *duplication_errors*
        # onto *errors*:
        unused_tokens_table: Dict[str, LetterToken]
        duplications_errors: List[Error]
        unused_tokens_table, duplication_errors = RS274.table_from_tokens(unused_tokens)
        errors: List[Error] = list()
        errors.extend(duplication_errors)

        # Flag when two or more *commands* are in the same group:
        conflict_errors: List[str]
        motion_command_name: str
        conflict_errors, motion_command_name = rs274.group_conflicts_detect(commands)
        errors.extend(conflict_errors)

        # Determine which *commands* want to use which *unused_tokens* using *unused_tokens_table*
        # and *letter_commands_table*.  The updated (and hopefully empty) *unused_tokens* list
        # is returned:
        bind_errors: List[Error]
        unused_letter_tokens: List[LetterToken]
        letter_commands_table: Dict[str, List[Command]] = (
          rs274.letter_commands_table_create(unused_tokens_table, commands, tracing=next_tracing))
        unused_letter_tokens, bind_errors = RS274.tokens_bind_to_commands(letter_commands_table,
                                                                          unused_tokens_table,
                                                                          tracing=next_tracing)
        errors.extend(bind_errors)

        # Perform any requested *tracing*:
        if tracing is not None:
            commands_text = RS274.commands_to_text(commands)
            unused_tokens_text = RS274.tokens_to_text(unused_tokens)
            print(f"{tracing}commands={commands_text} unused_tokens='{unused_tokens_text}'")

        # Sort the *commands* based on the *Group* key associated with the *command* name:
        groups_table: Dict[str, Group] = rs274.groups_table
        rs274.assign_group_keys()
        commands.sort(key=lambda command:
                      groups_table[command.Name].key if command.Name in groups_table else -1)

        # Wrap up any requested *tracing* and return results:
        if tracing is not None:
            commands_text = RS274.commands_to_text(commands)
            tokens_text = RS274.tokens_to_text(tokens)
            unused_tokens_text = RS274.tokens_to_text(unused_tokens)
            print(f"{tracing}<=RS274.commands_from_tokens('{tokens_text}')"
                  f"=>{commands_text}, *, '{unused_tokens_text}', '{motion_command_name}'")
        return commands, errors, unused_letter_tokens, motion_command_name

    # RS274.content_parse():
    def content_parse(self, content: str,
                      tracing: Optional[str] = None, trace: bool = False) -> List[Command]:
        """Parse an RS274 content and return resulting Command's.

        Arguments:
            content (str): The entire file content with lines
                separated by new-line character.
            tracing (Optional[str]): None for no tracing; otherwise
                the string to prefix to tracing output.

        Returns:
            List[Command]: The list of resulting Command's.

        """
        # Perform any requested *tracing*:
        next_tracing: Optional[str] = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>RS274.content_parse(*, '...') ")

        # Split *content* into *blocks* (i.e. lines) and parse them into *commands* that
        # are appended to *command_list*:
        rs274: RS274 = self
        lines: List[str] = content.split('\n')
        command: Command
        commands_list: List[List[Command]] = list()
        line_index: int
        line: str
        for line_index, line in enumerate(lines):
            # Parse *block* into *commands*:
            # print(f"Line[{line_index}]:'{line}'")
            rs274_commands: Optional[List[Command]]
            parse_errors: List[Error]
            # next_tracing = "Line[18]" if line_index == 18 else None
            rs274_commands, parse_errors = rs274.line_parse(line, tracing=next_tracing)
            trace_line: str
            if rs274_commands is None:
                trace_line = line.replace('(', '{').replace(')', '}')
                rs274_commands = [Command("( '{trace_line}' did not parse )")]
            if trace:
                trace_line = line.replace('(', '{').replace(')', '}')
                rs274_commands.insert(0, Command(f"( Line[{line_index}]: '{trace_line}' )"))
            if len(rs274_commands) <= 1:
                trace_line = line.replace('(', '{').replace(')', '}')
                rs274_commands.append(Command("( Empty commands parse '{trace_line}' )"))
            commands_list.append(rs274_commands)

            # Print out any errors:
            if len(parse_errors) >= 1 or next_tracing is not None:
                print("Line[{0}]='{1}'".format(line_index, line.strip('\r\n')))

                # Print the *errors*:
                error_index: int
                error: Error
                for error_index, error in enumerate(parse_errors):
                    print(f" Error[{error_index}]:'{error}'")

                # Dump the *commands*:
                if isinstance(rs274_commands, list):
                    commands: List[Command] = rs274_commands
                    index: int
                    for index, command in enumerate(commands):
                        assert isinstance(command, Command)
                        # print(f" Command[{index}]:{command}")

                print("")

        # This arcane command will flatten the *commands_list* into *flattened_commands*:
        flattened_commands: List[Command] = sum(commands_list, [])

        # Wrap up any requested *tracing* and return *flattened_commands*:
        if tracing is not None:
            print(f"{tracing}<=RS274.content_parse(*, '...')=>[...] ")
        return flattened_commands

    # RS274.commands_write():
    @staticmethod
    def commands_write(commands: List[Command], file_name: str):
        """Write commands to a file.

        Arguments:
            commands (List[Command]): The Command's to write out.
            file_name (str): The file to write out to.

        """
        # Write *commands* out to *file_name*
        with open(file_name, "w") as out_file:
            command: Command
            for command in commands:
                out_file.write(f"{command}\n")

    # RS274.drill_cycles_replace():
    @staticmethod
    def drill_cycles_replace(commands: List[Command]):
        """Replace G8* canned cycles with G0/G1 commands.

        Arguments:
            commands (List[Command]): List of Commands' to process.

        Returns:
            List[Command]: Updated list of Command's with G8x
                canned cylces replaced with G0/G1 commands.

        """
        # Sweep across *commands* special casing some of the G commands:
        nan: float = float("nan")  # Not A Number
        retract_mode: str = ""
        updated_commands: List[Command] = list()
        variables: Dict[str, Number] = dict()
        command: Command
        p: float = nan
        q: float = nan
        r: float = nan
        x: float = nan
        y: float = nan
        z: float = nan
        z_depth: float = nan

        variables['P'] = p
        variables['Q'] = q
        variables['R'] = r
        variables['X'] = x
        variables['Y'] = y
        variables['Z'] = z
        variables["Zdepth"] = z_depth

        for index, command in enumerate(commands):
            # Unpack *command*:
            name: str = command.Name
            parameters: Dict[str, Number] = command.Parameters
            if index < -1:
                print(f"Command[{index}]: BEFORE: "
                      f"command:'{command.Name}' "
                      f"parameters:{command.Parameters} "
                      f"x={variables['X']} y={variables['Y']} z={variables['Z']} "
                      f"z_depth={variables['Zdepth']}")

            # Update *variables*:
            key: str
            value: Number
            for key, value in parameters.items():
                if key == 'Z' and name in ("G82", "G83"):
                    key = "Zdepth"
                variables[key] = value

            if name in ("G98", "G99"):
                retract_mode = name
                updated_commands.append(command)
            elif name == "G80":
                variables['Zdepth'] = nan
                updated_commands.append(command)
            elif name in ("G82", "G83"):
                # Extract the needed values from *parameters* and *varibles*:
                # l = parameters['L'] if 'L' in parameters else (
                #    variables['L'] if 'L' in variables else None)
                p = float(variables['P'])
                q = float(variables['Q'])
                r = float(variables['R'])
                x = float(variables['X'])
                y = float(variables['Y'])
                z = float(variables['Z'])
                z_depth = float(variables['Zdepth'])

                # Provide *comment_command* to show all of the parameters used for the
                # drilling cycle:
                comment_command: Command = Command(f"({name} P:{p} Q:{q} R:{r} X:{x} Y:{y} Z:{z} "
                                                   f"Zdepth:{z_depth} retract_mode:{retract_mode})")
                updated_commands.append(comment_command)

                isnan = math.isnan
                if isnan(x) or isnan(y) or isnan(z) or isnan(z_depth) or isnan(q) or isnan(r):
                    comment_text = f"( {name} failed due to missing parameter )"
                    fail_comment = Command(comment_text)
                    updated_commands.append(fail_comment)
                else:
                    # Rapid (i.e. `G0`) to make sure that Z is at least the height of R:
                    z_drill: float = z
                    if z_drill < r:
                        z_drill = r
                        updated_commands.append(Command("G0", {'Z': z_drill}))

                    # Rapid (i.e. `G0`) to (*x*, *y*).  We assume that *z* is safe enough:
                    updated_commands.append(Command("G0", {'X': x, 'Y': y}))

                    # Dispatch on *name*:
                    if name == "G82":
                        # Simple drilling cycle:

                        # Rapid (i.e. `G0`) down to *r* if it makes sense:
                        if r < z:
                            z_drill = r
                            updated_commands.append(Command("G0", {'Z': r}))

                        # Drill (i.e. `G1`) down to *z_depth*:
                        updated_commands.append(Command("G1", {'Z': z_depth}))

                        # Do a dwell if *p* exists and is positive:
                        if not math.isnan(p) and p > 0.0:
                            updated_commands.append(Command("G4", {'P': p}))

                        # Rapid out of the hole to the correct retract height based
                        # on *retract_mode*:
                        z_drill = r if retract_mode == "G99" else z
                        updated_commands.append(Command("G0", {'Z': z_drill}))
                        variables['Z'] = z_drill
                    elif name == "G83":
                        # Keep pecking down until we get drilled down to *z_depth*:
                        delta: float = q / 10.0

                        # Do an initial rapid down to *r*:
                        z_drill = z
                        peck_index: int = 0
                        while z_drill > z_depth:
                            # print(f"Peck_Index[{peck_index}]:z_drill={z_drill}")

                            # Rapid (i.e. `G0`) up/down to *rapid_z*, where *rapid_z* will
                            # be at *r* on the first iteration, and multiples of *q* lower
                            # on subsequent iterations.  The *delta* offset enusures that
                            # the drill bit does not rapid into the hole bottom:
                            rapid_z: float = (r - (peck_index * q) + (0.0 if peck_index == 0
                                                                      else delta))
                            updated_commands.append(Command("G0", {'Z': rapid_z}))

                            # Drill (i.e. `G1`) down to *z_drill*, where *z_drill* is a
                            # multiple of *q* below *r*.  Never allow *z_drill* to get below
                            # *z_depth*:
                            z_drill = max(r - (peck_index + 1) * q, z_depth)
                            updated_commands.append(Command("G1", {'Z': z_drill}))

                            # Pause at the bottom of the hole if *p* is specified:
                            if not math.isnan(p) and p > 0:
                                updated_commands.append(Command("G4", {'P': p}))

                            # Retract all the way back to *r*:
                            updated_commands.append(Command("G0", {'Z': r}))

                            # Increment *peck_index* to force further down on the next cycle:
                            peck_index += 1

                        # Retract back up to *z* if we are in `G99` mode:
                        if retract_mode == "G98":
                            z_drill = z
                            updated_commands.append(Command("G0", {'Z': z_drill}))
                        variables['Z'] = z_drill
            elif name in ("G0", "G1", "G43"):
                if 'X' in parameters:
                    variables['X'] = float(parameters['X'])
                if 'Y' in parameters:
                    variables['Y'] = float(parameters['Y'])
                if 'Z' in parameters:
                    variables['Z'] = float(parameters['Z'])
                updated_commands.append(command)
                # print(f"command.Name='{command.Name}' command.Parameters={command.Parameters}")
            else:
                updated_commands.append(command)

            if index < -1:
                print(f"Command[{index}]: AFTER: "
                      f"command:'{command.Name}' "
                      f"parameters:{command.Parameters} "
                      f"x={variables['X']} y={variables['Y']} z={variables['Z']} "
                      f"z_depth={variables['Zdepth']}")

        return updated_commands

    # RS274.g28_remove():
    @staticmethod
    def g28_remove(commands: List[Command]):
        """Remove G28 commands from a list of Command's.

        Arguments:
            commands (List[Command]): List of Command's to process.

        Returns:
            List[Command]: List of updated Command's.

        """
        return [(Command("( G28/G28.1 removed )") if command.Name in ("G28", "G28.1") else command)
                for command in commands]

    # RS274.g91_remove():
    @staticmethod
    def g91_remove(commands: List[Command]):
        """Remove G91 commands from a list of Command's.

        Arguments:
            commands (List[Command]): The list of commands to process.

        Returns:
            List[Command]: The Command's list with G91 removed.

        """
        return [(Command("( G91 removed )") if command.Name == "G91" else command)
                for command in commands]

    # RS274.group_conflicts_detect()
    def group_conflicts_detect(self, commands: List[Command]) -> Tuple[List[Error], str]:
        """Detect group conflicts in a list of Command's.

        Arguments:
            commands (List[Command]):

        Returns:
            List[Error]: List of Error's.
            str: The motion command name (or "" for none).

        """
        # Grab some values from *rs274* (i.e. *self*):
        rs274: RS274 = self
        motion_group: Optional[Group] = rs274.motion_group
        groups_table: Dict[str, Group] = rs274.groups_table

        # Sweep through *commands* using *duplicates_table* to find commands that conflict with
        # one another because they are in the same *Group*:
        duplicates_table: Dict[str, Command] = dict()
        errors: List[Error] = list()
        motion_command_name: str = ""
        # g80_found: bool = False
        for command in commands:
            # Grab values from *command*:
            name: str = command.Name
            letter: str = name[0]
            # if name == "G80":
            #     g80_found = True

            # Find the *group* associated with *command*, or fail trying:
            group: Optional[Group]
            if name in groups_table:
                group = groups_table[name]
            elif letter in groups_table:
                group = groups_table[letter]
            else:
                # This should not happen:
                error: Error = f"'{name}' has no associated group"
                errors.append(error)
                group = None

            if group is not None:
                # Check for duplicates *group_name* in *duplicates_table*:
                group_name: str = group.short_name
                if group_name in duplicates_table:
                    # Flag commands from the same group as an error:
                    conflicting_command = duplicates_table[group_name]
                    error = (f"Command '{conflicting_command}' and '{command}' in the same block "
                             f"(i.e. line), they are in same '{group}' which is not allowed.")
                    errors.append(error)
                else:
                    duplicates_table[group_name] = command

                # Remember when we have found a *motion_command_name*:
                if group is motion_group:
                    motion_command_name = command.Name

        # if g80_found:
        #      motion_command_name = ""

        # Return the resulting *errors* and *motion_command_name*:
        return errors, motion_command_name

    # RS274.group_create():
    def group_create(self, short_name: str, title: str, before: str = "") -> Group:
        """Create a new named group.

        Arguments:
            short_name (str): The short G/M command name for the group.
                (e.g. "G0" for all motion commands, etc.)
            title (str): A more meaningful tile like ("Motion Commands")
            before (optional, str): The short name of the group, to
            insert the new group before.

        Returns:
            Group: The newly created Group is returned.

        """
        # Grab some values from *rs274* (i.e. *self*):
        rs274: RS274 = self
        groups_table: Dict[str, Group] = rs274.groups_table
        groups_list: List[Group] = rs274.groups_list

        # Create the *group*:
        group: Group = Group(rs274, short_name, title)

        # Stuff the new *group* into *groups_table* using *short_name* as the key:
        assert short_name not in groups_table
        groups_table[short_name] = group

        # Stuff *group *into *groups_list*.  If *before* is names a group that is already
        # in *groups_table*/*groups_list*, stuff the new *group* there.  Otherwise, append
        # it to the end of *groups_list*:
        if before == "":
            groups_list.append(group)
        else:
            assert before in groups_table
            before_group: Group = groups_table[before]
            before_index: int = groups_list.index(before_group)
            groups_list.insert(before_index, group)

        # All done.  Return *group*:
        return group

    # RS724.groups_create():
    def groups_create(self):
        """Create all of the needed groups."""
        # Grab the *groups* object from *rs274* (i.e. *self*):
        rs274: RS274 = self

        # The table below is largely derived from section 22 "G Code Order of Execution"
        # from the LinuxCNC G-Code overview documentation
        #
        #    [Order](http://linuxcnc.org/docs/html/gcode/overview.html#_g_code_order_of_execution):
        #
        #  There are some differences (e.g. M5/M9.)

        # O-word commands (optionally followed by a comment but no other words allowed on
        # the same line):

        # The *axes* variable lists all of the axis parameters:
        axes: str = "XYZABCUVWFS"

        # Line_number:
        line_number_group = rs274.group_create("N", "Line Number")
        line_number_group.letter_code("N", "Line Number")
        rs274.line_number_group = line_number_group

        # Comment (including message)
        comment_group: Group = rs274.group_create("(", "Comment")
        rs274.comment_group = comment_group

        # Set feed rate mode (G93, G94).
        feed_rate_group: Group = rs274.group_create("G93", "Feed Rate")
        feed_rate_group.g_code("G93", "", "Inverse Time Mode")
        feed_rate_group.g_code("G94", "", "Units Per Minute Mode")
        feed_rate_group.g_code("G95", "", "Units Per Revolution Mode")

        # Set feed rate (F).
        feed_group: Group = rs274.group_create("F", "Feed")
        feed_group.letter_code('F', "Set Feed Rate")

        # Set spindle speed (S).
        spindle_speed_group: Group = rs274.group_create("S", "Spindle")
        spindle_speed_group.letter_code('S', "Set Spindle Speed")

        # Select tool (T).
        tool_group: Group = rs274.group_create("T", "Tool")
        tool_group.letter_code('T', "Select Tool")

        # HAL pin I/O (M62-M68).

        # Change tool (M6) and Set Tool Number (M61).
        tool_change_group: Group = rs274.group_create("M6", "Tool Change")
        tool_change_group.m_code("M6", "T", "Tool Change")

        # Spindle on or off (M3, M4, M5).
        spindle_control_group: Group = rs274.group_create("M3", "Spindle Control")
        spindle_control_group.m_code("M3", "S", "Start Spindle Clockwise")
        spindle_control_group.m_code("M4", "S", "Start Spindle Counterclockwise")
        spindle_control_group.m_code("M19", "RQP", "Orient Spindle")
        spindle_control_group.m_code("M96", "DS", "Constant Surface Speed Mode")
        spindle_control_group.m_code("M97", "", "RPM Mode")

        # Save State (M70, M73), Restore State (M72), Invalidate State (M71).

        # Coolant on or off (M7, M8, M9).
        coolant_group: Group = rs274.group_create("M7", "Coolant")
        coolant_group.m_code("M7", "", "Enable Mist Coolant")
        coolant_group.m_code("M8", "", "Enable Flood Coolant")

        # Enable or disable overrides (M48, M49, M50, M51, M52, M53).
        feed_rate_mode_group: Group = rs274.group_create("M48", "Feed Rate Mode")
        feed_rate_mode_group.m_code("M48", "", "Enable Speed/Feed Override")
        feed_rate_mode_group.m_code("M49", "", "Disable Speed/Feed Override")
        feed_rate_mode_group.m_code("M50", "P", "Feed Override Control")
        feed_rate_mode_group.m_code("M51", "P", "Spindle Override Control")
        feed_rate_mode_group.m_code("M52", "P", "Adaptive Feed Control")
        feed_rate_mode_group.m_code("M53", "P", "Feed Stop Control")

        # User-defined Commands (M100-M199).

        # Dwell (G4).
        dwell_group: Group = rs274.group_create("G4", "Dwell")
        dwell_group.g_code("G4", "P", "Dwell")

        # Set active plane (G17, G18, G19).
        plane_selection_group: Group = rs274.group_create("G17", "Plane Selection")
        plane_selection_group.g_code("G17", "", "Use XY Plane")
        plane_selection_group.g_code("G18", "", "Use ZX Plane")
        plane_selection_group.g_code("G19", "", "Use YZ Plane")
        plane_selection_group.g_code("G17.1", "", "Use UV Plane")
        plane_selection_group.g_code("G18.1", "", "Use WU Plane")
        plane_selection_group.g_code("G19.1", "", "Use VW Plane")

        # Set length units (G20, G21).
        units_group: Group = rs274.group_create("G20", "Units")
        units_group.g_code("G20", "", "Use inches for length")
        units_group.g_code("G21", "", "Use millimeters for length")

        # Cutter radius compensation on or off (G40, G41, G42)
        group_name = "Cutter Radius Compensation Group"
        cutter_radius_compensation_group: Group = rs274.group_create("G40", group_name)
        cutter_radius_compensation_group.g_code("G40", "", "Compensation Off")
        cutter_radius_compensation_group.g_code("G41", "D", "Compensation Left")
        cutter_radius_compensation_group.g_code("G42", "D", "Compensation Right")
        cutter_radius_compensation_group.g_code("G41.1", "DL", "Dynamic Compensation Left")
        cutter_radius_compensation_group.g_code("G42.1", "DL", "Dynamic Compensation Right")

        # Cutter length compensation on or off (G43, G49)
        tool_length_offset_group: Group = rs274.group_create("G43", "Tool Offset Length")
        tool_length_offset_group.g_code("G43", "H", "Tool Length Offset")
        tool_length_offset_group.g_code("G43.1", axes, "Dynamic Tool Length Offset")
        tool_length_offset_group.g_code("G43.2", "H", "Apply Additional Tool Length Offset")
        tool_length_offset_group.g_code("G49", "", "Cancel Tool Length Compensation")

        # Coordinate system selection (G54, G55, G56, G57, G58, G59, G59.1, G59.2, G59.3).
        select_coordinate_system_group: Group = rs274.group_create("G54",
                                                                   "Select Machine Coordinates")
        select_coordinate_system_group.g_code("G54", "", "Select Coordinate System 1")
        select_coordinate_system_group.g_code("G55", "", "Select Coordinate System 2")
        select_coordinate_system_group.g_code("G56", "", "Select Coordinate System 3")
        select_coordinate_system_group.g_code("G57", "", "Select Coordinate System 4")
        select_coordinate_system_group.g_code("G58", "", "Select Coordinate System 5")
        select_coordinate_system_group.g_code("G59", "", "Select Coordinate System 6")
        select_coordinate_system_group.g_code("G59.1", "", "Select Coordinate System 7")
        select_coordinate_system_group.g_code("G59.2", "", "Select Coordinate System 8")
        select_coordinate_system_group.g_code("G59.3", "", "Select Coordinate System 9")

        # Set path control mode (G61, G61.1, G64)
        path_control_group: Group = rs274.group_create("G61", "Path Control")
        path_control_group.g_code("G61", "", "Exact Path Mode Collinear Allowed")
        path_control_group.g_code("G61.1", "", "Exact Path Mode No Collinear")
        path_control_group.g_code("G64", "", "Path Blending")

        # Set distance mode (G90, G91).
        distance_mode_group: Group = rs274.group_create("G90", "Distance Mode")
        distance_mode_group.g_code("G90", "", "Absolute Distance Mode")
        distance_mode_group.g_code("G91", "", "Incremental Distance Mode")
        distance_mode_group.g_code("G90.1", "", "Absolute Arc Distance Mode")
        distance_mode_group.g_code("G91.1", "", "Incremental Arc Distance Mode")

        # Set retract mode (G98, G99).
        retract_mode_group: Group = rs274.group_create("G98", "Retract Mode")
        retract_mode_group.g_code("G98", "", "Retract to Start")
        retract_mode_group.g_code("G99", "", "Retract to R")

        # Go to reference location (G28, G30) or change coordinate system data (G10) or
        # set axis offsets (G92, G92.1, G92.2, G94).
        # Reference Motion Mode:
        reference_motion_group: Group = rs274.group_create("G28", "Reference Motion")
        reference_motion_group.g_code("G28", axes, "Go/Set Position")
        reference_motion_group.g_code("G28.1", axes, "Go/Set Position")
        reference_motion_group.g_code("G30", axes, "Go/Set Position")
        reference_motion_group.g_code("G30.1", axes, "Go/Set Position")
        reference_motion_group.g_code("G92", "", "Reset Offsets")
        reference_motion_group.g_code("G92.1", "", "Reset Offsets")
        reference_motion_group.g_code("G92.2", "", "Reset Offsets")

        # Perform motion (G0 to G3, G33, G38.n, G73, G76, G80 to G89),
        # as modified (possibly) by G53:
        motion_group: Group = rs274.group_create("G0", "Motion")
        motion_group.g_code("G0", axes, "Rapid Move")
        motion_group.g_code("G1", axes, "Linear Move")
        motion_group.g_code("G2", axes + "IJKR", "CW Arc")
        motion_group.g_code("G3", axes + "IJKR", "CCW Arc")
        motion_group.g_code("G5", axes + "IJPQ", "Cubic Spline")
        motion_group.g_code("G5.1", axes + "IJ", "Quadratic Spline")
        motion_group.g_code("G5.2", axes + "PL", "NURBS")
        motion_group.g_code("G33", axes + "K", "Spindle Synchronized Motion")
        motion_group.g_code("G33.1", axes + "K", "Spindle Synchronized Motion")
        motion_group.g_code("G38.2", axes, "Probe toward contact, signal failure")
        motion_group.g_code("G38.3", axes, "Probe toward contact")
        motion_group.g_code("G38.4", axes, "Probe away from contact, signal failure")
        motion_group.g_code("G38.5", axes + "K", "Probe away from contact loss")
        rs274.motion_group = motion_group

        # Canned Cycles are really motion commands (G80 disables canned cyles in a separate group):
        motion_group.g_code("G81", axes + "RLP", "Drilling Cycle")
        motion_group.g_code("G82", axes + "RLP", "Drilling Cycle, Dwell")
        motion_group.g_code("G83", axes + "RLQ", "Drilling Cycle, Peck")
        motion_group.g_code("G73", axes + "RLQ", "Drilling Cycle, Chip Breaking")
        motion_group.g_code("G85", axes + "RLP", "Boring Cycle, Feed Out")
        motion_group.g_code("G89", axes + "RLP", "Boring Cycle, Dwell, Feed Out")
        motion_group.g_code("G76", axes + "PIJRKQHLE", "Threading Cycle")

        # Turning off a canned cycle must occur after the canned cycle:
        canned_cycles_group: Group = rs274.group_create("G80", "Canned Cycles")
        canned_cycles_group.g_code("G80", "", "Cancel Canned Cycle")

        # Spindle/Coolant stopping:
        spindle_coolant_stopping_group: Group = rs274.group_create("M5", "Spinde/Collant Stopping")
        spindle_coolant_stopping_group.m_code("M5", "", "Stop Spindle")
        spindle_coolant_stopping_group.m_code("M9", "", "Stop Coolant")

        # Stop (M0, M1, M2, M30, M60).
        stopping_group: Group = rs274.group_create("M0", "Machine Stopping and/or Pausing")
        stopping_group.m_code("M0", "", "Program Pause")
        stopping_group.m_code("M1", "", "Program End")
        stopping_group.m_code("M2", "", "Program Pause")
        stopping_group.m_code("M30", "", "Change Pallet and Program End")
        stopping_group.m_code("M60", "", "Program Change Pallet Pause")

    # RS274.group_show():
    @staticmethod
    def groups_show(groups: List[Group], label: str):
        """Print out a labled list of Group's for debugging."""
        print(label)
        index: int
        group: Group
        for index, group in enumerate(groups):
            templates: Dict[str, Template] = group.templates
            name: str
            template_text: str = ",".join(templates.keys())
            print(f"[{index}]:{group.short_name}({template_text})")

    # RS274.letter_commands_table_create():
    def letter_commands_table_create(self, unused_tokens_table: "Dict[str, LetterToken]",
                                     commands: List[Command],
                                     tracing: Optional[str] = None) -> Dict[str, List[Command]]:
        """Return a table used for token to command binding.

        Arguments:
            unused_tokens_table (Dict[str, LetterToken]): A table of
                tokens keyed by the token letter
                (e.g key=letter_token.letter).
            commands (List[Command]): A list of commands to bind to the
                tokens.
            tracing (Optionial[str]): None for no tracing; otherwise
                the string to prefix to tracing output.

        Returns:
            Dict[str, List[Command]]: A table keyed by parameter letter
                lists the Command(s) that need to use parameter letter.

        """
        # Perform any requested *tracing*:
        if tracing is not None:
            unused_tokens_text: str = RS274.tokens_to_text(list(unused_tokens_table.values()))
            commands_text: str = RS274.commands_to_text(commands)
            print(f"{tracing}=>RS274.letter_commands_table_create("
                  f"{unused_tokens_text}, {commands_text})")

        # Start filling up *letter_template_table*:
        rs274: RS274 = self
        letter_commands_table: Dict[str, List[Command]] = dict()
        templates_table: Dict[str, Template] = rs274.templates_table
        letter_index: int
        letter: str
        for letter_index, letter in enumerate(unused_tokens_table.keys()):
            # Perform any requested *tracing*:
            # if tracing is not None:
            #     print(f"{tracing}Letter[{letter_index}]:'{letter}'")

            # Now sweep through *commands* trying to figure out which command wants which
            # unused token:
            command_index: int
            command: Command
            for command_index, command in enumerate(commands):
                # Unpack *command*:
                name: str = command.Name
                # if tracing is not None:
                #     print(f"{tracing} Command[{command_index}]:{command}")

                # Look up the *template* from *templates_table*
                if name in templates_table:
                    template = templates_table[name]
                    # if tracing is not None:
                    #     print(f"{tracing}  Template[{command_index}]:{template}")

                    # Register *command* is needing *template_letter* from *template*:
                    template_index: int
                    template_letter: str
                    for template_index, template_letter in enumerate(template.parameters.keys()):
                        # if tracing is not None:
                        #     print(f"{tracing}   TemplateL[{template_index}]:'{template_letter}'")
                        if letter == template_letter:
                            # We have a match, make sure we have list and append *command* to it:
                            if letter not in letter_commands_table:
                                letter_commands_table[letter] = list()
                            letter_commands_table[letter].append(command)
                # else: Ignore *command* that does not have a *template*:

        # Wrap up any requested *tracing* and return *letter_commands_table*:
        if tracing is not None:
            unused_tokens_text = RS274.tokens_to_text(list(unused_tokens_table.values()))
            commands_text = RS274.commands_to_text(commands)
            pairs: List[str] = list()
            sub_commands: List[Command]
            for letter, sub_commands in letter_commands_table.items():
                sub_commands_text = RS274.commands_to_text(sub_commands)
                pairs.append(f"'{letter}': {sub_commands_text}")
            pairs_text: str = '{' + ', '.join(pairs) + '}'
            print(f"{tracing}<=RS274.letter_commands_table_create("
                  f"{unused_tokens_text}, {commands_text})=>{pairs_text}")
        return letter_commands_table

    # RS274:line_parse():
    def line_parse(self, line: str,
                   tracing: Optional[str] = None) -> Tuple[Optional[List[Command]], List[Error]]:
        """Parse one line of CNC code into a list of commands.

        Args:
            line (str): The line of CNC code to parse. There
                be no trailing new-line character.
            tracing: (Optionial[str]): Either *None* for no tracing, or a
                tracing indentation string (usually a string of spaces.)

        Returns:
            commands (List[Command]): A list of *Command*'s for each
                CNC command in *block*.  This returned list is empty if there
                are no commands.
            errors (List[Error]): A list of error strings.

        """
        # Perform any requested *tracing*:
        next_tracing: Optional[str] = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>RS274.line_parse('{line}', *)")

        # Grab *previous_motion_command_name* from *rs274* (i.e. *self*):
        rs274: RS274 = self
        previous_motion_command_name = rs274.motion_command_name
        if tracing is not None:
            print(f"{tracing}previous_motion_command_name='{previous_motion_command_name}'")

        # The final results from this method are stored in the variables below.  The
        # *final_motion_command_name* is stuffed back into *rs274* (i.e. *self*) at the end:
        final_commands: List[Command]
        final_errors: List[Error]
        final_motion_command_name: str

        # Start by tokenizing the *block* (i.e. a line of G-code) into *tokens*:
        tokens: List[Token]
        tokenize_errors: List[str]
        tokens, tokenize_errors = rs274.line_tokenize(line)

        # We only continue with the parsing if there were no *tokenize_errors*:
        result_message: str = ""
        if tokenize_errors:
            # We have *tokenize_errors*, so we stop the process here:
            final_commands = list()
            final_errors = tokenize_errors
            final_motion_command_name = previous_motion_command_name
            result_message = f"{len(tokenize_errors)} tokenization errors"
        else:
            # Now we try to parse *tokens* into a list of *final_commands*.  First we try it
            # without adding on a "sticky" motion G command.  If that fails, we try to add
            # on a "sticky" motion G command, and see if the fixes things up:

            # Do the first attempt at parsing tokens into *final_commands*:
            commands1: List[Command]
            errors1: List[Error]
            unused_tokens1: List[LetterToken]
            motion_command_name1: str
            (commands1, errors1, unused_tokens1,
             motion_command_name1) = rs274.commands_from_tokens(tokens, tracing=next_tracing)
            if tracing is not None:
                commands1_text: str = RS274.commands_to_text(commands1)
                unused_tokens1_text: str = RS274.tokens_to_text(unused_tokens1)
                print(f"{tracing}commands1=[{commands1_text}] "
                      f"error1={errors1} "
                      f"unused_tokens1=[{unused_tokens1_text}] "
                      f"motion_command_name1='{motion_command_name1}'")

            # If there are no *errors1* and no *unused_tokens*, we have succeeded:
            succeeded: bool = False
            if not errors1 and not unused_tokens1:
                # We *succeeded* on the first parse attempt, so we can wrap up the result
                # variables being careful to use the correct value for *final_motion_command_name*:
                final_commands = commands1
                final_errors = errors1
                final_motion_command_name = (motion_command_name1 if motion_command_name1
                                             else previous_motion_command_name)
                result_message = "First parse attempt succeeded"
            elif unused_tokens1 and motion_command_name1 == "":
                # The first parse of *tokens* had some *unused_tokens* and there was no
                # *motion_command1" (e.g. G0, G3, G82, etc.) found. It makes sense to try
                # again by attempting to fix the problem by adding a *motion_token* to
                # the *tokens* and attempting to reparse:

                # There are two candidates for the *motion_token* we need to compute.
                # The most obvious is *previous_motion_command_name*.  The less obvious
                # one occurs when a G88 (Cancel Canned Cycle) is encountered.  In that
                # cas we absolutely do not want to do any more of *previous_motion_command_name*,
                # but instead want to to a G0 rapid command instead.

                # The first step is to figur out if we *have_g80*:
                have_g80: bool = False
                token: Token
                for token in tokens:
                    if isinstance(token, LetterToken):
                        if token.letter == 'G' and token.number == 80:
                            have_g80 = True
                            break
                if tracing is not None:
                    print(f"{tracing}have_g80={have_g80} "
                          f"previous_motion_command_name='{previous_motion_command_name}'")

                # If we *have_g80* or we have a *previous_motion_command_name*, we create a
                # *motion_token* for a second attempt at parsing *tokens*:
                if have_g80 or previous_motion_command_name:
                    # Create the appropriate *motion_token* to append to *tokens* and prior to
                    # attempting to reparse *tokens*.  The G80->G0 conversion take precedence
                    # over the *previoous_motion_command_name*:
                    motion_token: LetterToken
                    if have_g80:
                        motion_token = LetterToken(0, 'G', 0)
                    else:
                        # Tediously convert *previous_motion_command_name* into *motion_token*:
                        assert len(previous_motion_command_name) >= 2
                        letter: str = previous_motion_command_name[0]
                        assert letter in "G"
                        number_text: str = previous_motion_command_name[1:]
                        number: Number = (float(number_text) if '.' in number_text
                                          else int(number_text))
                        motion_token = LetterToken(0, letter, number)

                    # With *motion_token* appended to *tokens*, we can try to reparse *tokens*:
                    tokens.append(motion_token)
                    commands2: List[Command]
                    errors2: List[Error]
                    unused_tokens2: List[LetterToken]
                    motion_command_name2: str
                    commands2, errors2, unused_tokens2, motion_command_name2 = \
                        rs274.commands_from_tokens(tokens, tracing=next_tracing)
                    if tracing is not None:
                        print(f"{tracing}modified tokens={RS274.tokens_to_text(tokens)}")
                        print(f"{tracing}commands2={RS274.commands_to_text(commands2)}")
                        print(f"{tracing}unused_tokens2={RS274.tokens_to_text(unused_tokens2)}")
                        print(f"{tracing}motion_command_name2='{motion_command_name2}'")

                    # If there are no errors and no unused tokens, we have *succeeded*:
                    if not errors2 and not unused_tokens2:
                        # If the G80 caused us to add a G0 to *tokens*, we need to
                        # adjust the resulting commands list so that the G80 occurs *before*
                        # the G0 command:
                        succeeded = True
                        if have_g80:
                            # Sweep through *commands2* finding the *g80_index* and the *g0_index*:
                            g0_index: int = -1
                            g80_index: int = -1
                            index: int
                            command: Command
                            for index, command in enumerate(commands2):
                                command_name: str = command.Name
                                if command_name == "G0":
                                    g0_index = index
                                elif command_name == "G80":
                                    g80_index = index
                            assert g0_index >= 0 and g80_index >= 0

                            # Now move *g80_command* to be in front of *g0_command* in *commands2*:
                            if g80_index > g0_index:
                                g80_command: Command = commands2[g80_index]
                                del commands2[g80_index]
                                commands2.insert(g0_index, g80_command)

                        # We have succeeded by adding *motion_command_name* to *tokens*:
                        final_commands = commands2
                        final_errors = errors2
                        assert motion_command_name2
                        final_motion_command_name = motion_command_name2
                        result_message = "Second parse attempt succeeded"

            # We we have not *succeeded*, we return the results from the first parse attempt,
            # with an additional error message:
            if not succeeded:
                # Append the *unused_tokens_error* to *errors1*:
                if len(unused_tokens1) >= 1:
                    unused_tokens_text: str = RS274.tokens_to_text(unused_tokens1)
                    unused_tokens_error: Error = f"'{unused_tokens_text}' is/are unused"
                    errors1.append(unused_tokens_error)
                final_commands = commands1
                final_errors = errors1
                final_motion_command_name = (motion_command_name1 if motion_command_name1
                                             else previous_motion_command_name)
                result_message = "Neither parse attempt succeeded"

        # Now we can stuff *final_model_motion_name* back into *rs274*:
        rs274.motion_command_name = final_motion_command_name
        if tracing is not None:
            print(f"{tracing}after: final_motion_command_name='{final_motion_command_name}'")
            print(f"{tracing}{result_message}")

        # Wrap up any requested *tracing* and return *final_commands*:
        if tracing is not None:
            final_commands_text = RS274.commands_to_text(final_commands)
            print(f"{tracing}<=RS274.line_parse('{line}', *)=>{final_commands_text},{final_errors}")
        return final_commands, final_errors

    # RS274:line_tokenize():
    def line_tokenize(self, line: str) -> "Tuple[List[Token], List[Error]]":
        """Convert line of G code into Token's.

        Arguments:
            line (str): A line of G-code with no new-line character.

        Returns:
            List[Token]: A list of parsed tokens.
            List[Error]: A list of token parsing errors.

        """
        # Grab some values from *rs274* (i.e. *self*):
        rs274: RS274 = self
        white_space: str = rs274.white_space
        match_routines: Tuple[Callable] = rs274.token_match_routines

        # Scan across *line* until all *tokens* have been extracted:
        tokens: List[Token] = list()
        errors: List[str] = list()
        line_size: int = len(line)
        index: int = 0
        while index < line_size:
            # Skip over *white_space*:
            if line[index] in white_space:
                index += 1
            else:
                # Search for a *token* by sequentially invoking each *match_routine* in
                # *match_routines*:
                matched: bool = False
                token: Optional[Token] = None
                match_routine: Callable[[str, int], Token]
                for match_routine in match_routines:
                    token = match_routine(line, index)
                    if isinstance(token, Token):
                        # We have a match, so remember *token*:
                        matched = True
                        tokens.append(token)
                        # Update *index* to point to the next token:
                        index = token.end_index
                        break
                if not matched:
                    remaining: str = line[index:]
                    error: str = f"Can not parse '{remaining}'"
                    errors.append(error)
                    break

        return tokens, errors

    # RS274.n_remove():
    @staticmethod
    def n_remove(commands: List[Command]) -> List[Command]:
        """Return a copy of commands with N codes removed."""
        return [command for command in commands if command.Name[0] != 'N']

    # RS274.table_from_tokens():
    @staticmethod
    def table_from_tokens(tokens: "List[Token]") -> "Tuple[Dict[str, LetterToken], List[Error]]":
        """Convert tokens into a dict with list duplicate errors list.

        Arguments:
            tokens (List[Token]): The list of tokens to process.

        Returns:
            Dict[str, Token]: The token dictionary keyed on token name/letter.
            List[Error]: List of errors.

        """
        # Fill up *tokens_table* with each *token* checking for duplicates:
        errors: List[Error] = list()
        letter_tokens_table: Dict[str, LetterToken] = dict()
        for token in tokens:
            token.recatagorize(letter_tokens_table, errors)

        # Return *letter_tokens_table* and *errors*:
        return letter_tokens_table, errors

    # RS274.token_match_tests():
    @staticmethod
    def token_match_tests():
        """Run token match tests."""
        BracketToken.test()
        CommentToken.test()
        LetterToken.test()
        OLetterToken.test()

    # RS274.tokens_bind_to_commands():
    @staticmethod
    def tokens_bind_to_commands(letter_commands_table: Dict[str, List[Command]],
                                unused_tokens_table: "Dict[str, LetterToken]",
                                tracing: Optional[str] = None) -> ("Tuple[List[LetterToken],"
                                                                   "List[Error]]"):
        """Merge unused tokens into pending commands.

        Arguments:
            letter_commands_table (Dict[str, List[Command]): A dict
                of parameters keyed by parameter letter with values
                list the Command's that use the parameter letter.
            unused_tokens_table (Dict[str, LetterToken)]: A dict of tokens
                keyed by parameter letter that are available for
                binding to commands.
            tracing

        """
        # Perform any requested *tracing*:
        if tracing is not None:
            letters_text: str = " ".join([f"{letter}" for letter in letter_commands_table.keys()])
            unused_tokens_text: str = RS274.tokens_to_text(list(unused_tokens_table.values()))
            print(f"{tracing}=>RS274.tokens_bind_to_commands("
                  f"'{letters_text}', '{unused_tokens_text}')")

        # Now sweep through *letter_commands_table* looking for *errors* and attaching
        # each appropriate *token* to a *command* (thereby making them used tokens):
        errors: List[Error] = list()
        letter: str
        letter_commands: List[Command]
        for letter, letter_commands in letter_commands_table.items():
            # Each *letter* in *letter_commands_table has an associated list of *Command*'s:
            # Dispatch on *letter_commands_size*:
            letter_commands_size: int = len(letter_commands)
            if letter_commands_size == 0:
                # *letter* is unused, so there is nothing to do:
                pass
            elif letter_commands_size == 1:
                # Remove the *token* associated with *letter* from *unused_tokens_table*:
                token: LetterToken = unused_tokens_table[letter]
                del unused_tokens_table[letter]

                # Take the *token* value and put it into *command*:
                command: Command = letter_commands[0]
                parameters: Dict[str, Number] = command.Parameters
                parameters[letter] = token.number_get()
            elif letter_commands_size >= 2:
                # We have a conflict, so we generate an *error*:
                command_names: List[str] = [command.Name for command in letter_commands]
                conflicting_commands: str = ", ".join(command_names)
                error: str = (f"Commands '{conflicting_commands}' need to use the "
                              f"'{letter}' parameter")
                errors.append(error)

        # Generate an updated list of *unused_tokens* from what is left in *unused_tokens_table*:
        unused_tokens: List[LetterToken] = list(unused_tokens_table.values())

        # Wrap up any requested *tracing* and return *unused_tokens* list with *errors*:
        if tracing is not None:
            unused_tokens_text = RS274.tokens_to_text(unused_tokens)
            print(f"{tracing}<=RS274.tokens_bind_to_commands(*, *)=>{unused_tokens_text}, *")
        return unused_tokens, errors

    # RS274.tokens_to_text():
    @staticmethod
    def tokens_to_text(tokens):
        """Return turn token list as a string."""
        return '[' + ", ".join([f"{token}" for token in tokens]) + ']'


class Template:
    """Represents a G/M code that is a member of a Group."""

    # Template.__init__():
    def __init__(self, name: str, parameter_letters: str, title: str):
        """Initialize a template with a *name*, *parameter_letters* and *title*.

        Arguments:
            name (str): The name of the template M/G code (e.g. "G0",
                "M3", etc.)
            parameters_letters (str): A list of parameters that this
                command takes.  Example: The "G0" command can take any
                of axis parameters "ABCUVWXYZ".
            title (str): A description title for documentation purposes.

        """
        # Create a *parameters* dictionary and fill it in from *parameter_letters*:
        parameters: Dict[str, Number] = dict()
        parameter_letter: str
        for parameter_letter in parameter_letters:
            parameters[parameter_letter] = 0

        # Stuff arguments into *template* (i.e. *self*):
        template: Template = self
        self.name: str = name
        self.parameters: Dict[str, Number] = parameters
        self.title: str = title
        template = template

    # Template.__str__():
    def __str__(self) -> str:
        """Return a string representation of a Template."""
        # Grab some values from *template* (i.e. *self*):
        template: Template = self
        name: str = template.name
        parameters: Dict[str, Number] = template.parameters
        title: str = template.title

        # Create a *sorted_parameters_letters*:
        sorted_parameters_letters = "".join(sorted(list(parameters.keys())))

        # Generate and return the final *result*:
        result: str = f"{name} '{sorted_parameters_letters}' '{title}'"
        return result


# Token:
class Token:
    """Represent on token on a G-code line (e.g. "M7", "T1", "X3.1")."""

    # Token.__init__():
    def __init__(self, end_index: int, tracing: Optional[str] = None):
        """Initialize a Token to have a position.

        Arguments:
            end_index (int) : The position in the line where the
                token ends.
            tracing (Optional[str]): None for no tracing; otherwise
                the string to prefix to tracing output.

        """
        # Perform any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>Token.__init__(*, {end_index})")

        # Fill in the *token* object (i.e. *self*) from the routine arguments:
        token: Token = self
        self.end_index: int = end_index
        token = token

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Token.__init__(*, {end_index})")

    # Token.__str__():
    def __str__(self) -> str:
        """Return text string for token."""
        return "?"

    # Token.catagorize():
    def catagorize(self, commands: List[Command], unused_tokens: "List[Token]"):
        """Place holder routine that fails."""
        # If this routine is called, we have missed writing a *catagorize* method somewhere:
        token: Token = self
        assert False, f"No catagorize() method for {type(token)}"

    # Token.letter_get():
    def letter_get(self) -> str:
        """Return the associated number value."""
        token: Token = self
        assert False, f"Token.letter_get(): {token.__class__.__name__}.get_number() dos not exist!"
        return "Error"

    # Token.number_get():
    def number_get(self) -> Number:
        """Return the associated number value."""
        token: Token = self
        assert False, f"Token.number_get(): {token.__class__.__name__}.get_number() dos not exist!"

    # LetterToken.recatagorize():
    def recatagorize(self, letter_tokens_table: "Dict[str, LetterToken]", errors: List[Error]):
        """Sort token into either *letter_tokens_table* or and error.

        Arguments:
            letter_tokens_table (Dict[str, LetterToken]): The place to
                store unique parameters keyed by parameter letter.
            errors (List[Error]): An error list to append error
                messages to.

        """
        # This method catches all non *LetterToken*'s and converts them into *errors*:
        token: Token = self
        error: Error = f"'{token}' is not a parameter"
        errors.append(error)


# BracketToken:
class BracketToken(Token):
    """Represent a NIS RS274 indirect argument (e.g "[123.456]")."""

    # BracketToken.__init__():
    def __init__(self, end_index: int, value: Number, tracing: Optional[str] = None):
        """Initialize a BracketToken to have a value.

        Arguments:
            end_index (int): The end position of token in the line.
            value (Number): The number value between the brackets.
            tracing (Optional[str]): None for no tracing; otherwise
                the string to prefix to tracing output.

        """
        # Perform an requested *tracing*:
        next_tracing: Optional[str] = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>BracketToken.__init__(*, {end_index}, {value})")

        # Initialize the *token_bracket* (i.e. *self*):
        bracket_token: BracketToken = self
        super().__init__(end_index, tracing=next_tracing)
        self.value: Number = value
        bracket_token = bracket_token

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>BracketToken.__init__(*, {end_index}, {value})")

    # BracketToken.__str__():
    def __str__(self) -> str:
        """Convert BracketToken to human readable string."""
        token_bracket: BracketToken = self
        return "[{0}]".format(token_bracket.value)

    # BracketToken.catagorize():
    def catagorize(self, commands: List[Command], unused_tokens: List[Token]):
        """Catagorize the bracket token into unused tokens."""
        # Currently nobody uses a *bracket_token* (i.e. *self*):
        bracket_token: BracketToken = self
        unused_tokens.append(bracket_token)

    # BracketToken.match():
    @staticmethod
    def match(line: str,
              start_index: int,
              tracing: Optional[str] = None) -> "Optional[BracketToken]":
        """Parse a BracketToken from line.

        Arguments:
            line (str): The line of G-code to parse from.
            start_index (int): The character position to start at.

        Returns:
            Optional[BracketToken]: The resulting BracketToken
            or None if no match found.

        """
        # Perform requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{tracing}=>BracketToken.match('{line}', {start_index}")

        # Set *end_index* to index after the closing square bracket when we have succeeded.
        # If *end_index* is less than zero, we have not successfully matched a bracket token:
        end_index: int = -1

        # We must start with a '[':
        line_size: int = len(line)
        if line_size > 0 and line[start_index] == '[':
            white_space: str = " \t"
            have_decimal_point: bool = False
            have_digit: bool = False
            have_number: bool = False

            # *number_start* and *number_end* point to the character span of the number
            # excluding brackets and white space.  The span is only valid if both are positive:
            number_start: int = -1
            number_end: int = -1

            # Sweep across the remainder of *line* starting after the opening '[':
            index: int
            for index in range(start_index + 1, len(line)):
                # Dispatch on *character*:
                character: str = line[index]
                if character in white_space:
                    # White space is allowed on both sides of the number between the square
                    # brackets.  What is not allowed is having more than one number between
                    # the square brackets:
                    if number_end >= 0:
                        have_number = True
                elif character == ']':
                    # We have found the closing ']':
                    if have_digit:
                        # Token successfully matched:
                        have_number = True
                        end_index = index + 1
                    # else: Error: no number between brackets:
                    break
                elif character.isdigit():
                    # Detect multiple numbers:
                    if have_number:
                        # Error: duplicate numbers:
                        break
                    # Record that we have a digit:
                    have_digit = True
                    if number_start < 0:
                        number_start = index
                    number_end = index + 1
                elif character == '.':
                    # We have a decimal point:
                    if have_number or have_decimal_point:
                        # Error: Duplicate decimal point or dupicate number:
                        break
                    have_decimal_point = True
                    if number_start < 0:
                        number_start = index
                    number_end = index + 1
                elif character == '-':
                    # We have a minus sign, which must be at the beginning of the number:
                    if number_start < 0:
                        # This is the first character of the number:
                        number_start = index
                        number_end = index + 1
                    else:
                        # Error: minus sign in the middle of a number:
                        break
                else:
                    # Error: Unrecognized character that is not one of "[-.0123456789]":
                    break

        # We have succecded when *end_index* is positive:
        bracket_token: Optional[BracketToken] = None
        if end_index >= 0:
            bracket_token = BracketToken(end_index, float(line[number_start:number_end]))

        # Wrap up any requested *tracing* and return *token*:
        if tracing is not None:
            print("{tracing}<=BracketToken.match('{line}', {start_index2})=>{token}")
        return bracket_token

    # BracketToken.number_get():
    def number_get(self) -> Number:
        """Return the bracket token number value."""
        # Return the number associated with *bracket_token*:
        bracket_token: BracketToken = self
        number: Number = bracket_token.value
        return number

    # BracketToken.test():
    @staticmethod
    def test():
        """Run some unit tests for TestBracket."""
        # Success tests:
        assert BracketToken.test_success("[0]", 0.0)
        assert BracketToken.test_success("[1]", 1.0)
        assert BracketToken.test_success("[1.]", 1.0)
        assert BracketToken.test_success("[1.0]", 1.0)
        assert BracketToken.test_success("[-1]", -1.0)
        assert BracketToken.test_success("[-1.]", -1.0)
        assert BracketToken.test_success("[-1.0]", -1.0)
        assert BracketToken.test_success("[ 0]", 0.0)
        assert BracketToken.test_success("[0 ]", 0.0)
        assert BracketToken.test_success("[ 0 ]", 0.0)
        assert BracketToken.test_success("[.1234]", 0.1234)
        assert BracketToken.test_success("[1.234]", 1.234)
        assert BracketToken.test_success("[12.34]", 12.34)
        assert BracketToken.test_success("[123.4]", 123.4)
        assert BracketToken.test_success("[1234.]", 1234.0)

        # Fail tests:
        assert not isinstance(BracketToken.match("", 0), BracketToken)
        assert not isinstance(BracketToken.match("(comment)", 0), BracketToken)
        assert not isinstance(BracketToken.match("o1234 call", 0), BracketToken)
        assert not isinstance(BracketToken.match("x23", 0), BracketToken)
        assert not isinstance(BracketToken.match("[", 0), BracketToken)
        assert not isinstance(BracketToken.match("[]", 0), BracketToken)
        assert not isinstance(BracketToken.match("[-]", 0), BracketToken)
        assert not isinstance(BracketToken.match("[.]", 0), BracketToken)
        assert not isinstance(BracketToken.match("[-.]", 0), BracketToken)
        assert not isinstance(BracketToken.match("[1-]", 0), BracketToken)
        assert not isinstance(BracketToken.match("[1-0]", 0), BracketToken)
        assert not isinstance(BracketToken.match("[.1.]", 0), BracketToken)
        assert not isinstance(BracketToken.match("[.1.]", 0), BracketToken)
        assert not isinstance(BracketToken.match("[1 1]", 0), BracketToken)
        assert not isinstance(BracketToken.match("[1 1 ]", 0), BracketToken)
        assert not isinstance(BracketToken.match("[ 1 1]", 0), BracketToken)
        assert not isinstance(BracketToken.match("[ 1 1 ]", 0), BracketToken)
        assert not isinstance(BracketToken.match("[ 1 . ]", 0), BracketToken)
        assert not isinstance(BracketToken.match("[ 1 - ]", 0), BracketToken)

    # BracketToken.test_success():
    @staticmethod
    def test_success(line: str, value: float):
        """Verify line of G-code matchs a BracketToken.

        Arguments:
            line (str): The line of G-code to match against.
            value (float): The value inside of the brackets to match.

        """
        # Tack some different termiators on the end of *block* to test end cases:
        terminators: List[str] = ["", " ", "[", "]", "x"]
        terminator: str
        for terminator in terminators:
            # Now verify that *block* is matched and the resulting *token* is correct:
            bracket_token: Optional[BracketToken] = BracketToken.match(line + terminator, 0)
            assert isinstance(bracket_token, BracketToken)
            assert bracket_token.end_index == len(line)
            assert bracket_token.value == value
        return True


# CommentToken:
class CommentToken(Token):
    """Represents an RS274 comment (e.g. '( comment )'."""

    # CommentToken.__init__:
    def __init__(self, end_index: int, is_first: bool, comment: str,
                 tracing: Optional[str] = None):
        """Initialze a CommentToken.

        Arguments:
            end_index (int): The line position where the token ends.
            is_first (bool): True if at beginning of line.
            comment (str): The actual comment including parenthesis.
            tracing (Optional[str]): None for no tracing; otherwise
                the string to prefix to tracing output.

        """
        # Preform any requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{tracing}=>CommentToken.__init__(*, {end_index}, {is_first}, '{comment}')")

        # Initialize the *token_comment* (i.e. *self*):
        comment_token: CommentToken = self
        super().__init__(end_index)
        self.is_first: bool = is_first
        self.comment: str = comment
        comment_token = comment_token

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{tracing}<=CommentToken.__init__(*, {end_index1}, {is_first}, {comment})")

    # CommentToken.__str__():
    def __str__(self):
        """Return CommentToken as string."""
        comment_token: CommentToken = self
        return comment_token.comment

    # CommentToken.catagorize():
    def catagorize(self, commands: List[Command], unused_tokens: List[Token]):
        """Catagorize a comment token into commands list.

        Arguments:
            commands (List[Command]): Command's list to
                catagorize CommentToken to.
            unused_tokens (List[Tokens]): Unused.

        """
        # Currently nobody uses a *bracket_token* (i.e. *self*):
        comment_token: CommentToken = self
        comment: str = comment_token.comment
        comment_command: Command = Command(comment)
        commands.append(comment_command)

    # CommentToken.match():
    @staticmethod
    def match(line: str, start_index: int) -> "Optional[CommentToken]":
        """Match an RS274 comment (e.g. '( comment )').

        Arugments:
            line (str): The line to parse comment from.
                start_index (int): The position to start parsing at.

        Returns:
            Optional[CommentToken]: None if no match found;
                othewise, a new CommentToken.

        """
        # We most start with a open parenthesis:
        end_index: int = -1
        is_first: bool = start_index == 0
        line_size: int = len(line)
        if line_size > 0 and line[start_index] == '(':
            # Scan looking for the closing parenthesis:
            index: int
            for index in range(start_index + 1, line_size):
                if line[index] == ')':
                    # We have successfully matched a parenthesis:
                    end_index = index + 1
                    break

        # We have have successfully matached a comment if *end_index* is positive:
        comment_token: Optional[CommentToken] = None
        if end_index >= 0:
            comment_token = CommentToken(end_index, is_first, line[start_index:end_index])
        # print("CommentToken.match(*, '{0}', {1}) => {2}".format(line, start_index, token))
        return comment_token

    # CommentToken.test():
    @staticmethod
    def test():
        """Run some tests for CommentToken's."""
        # Success tests:
        assert CommentToken.test_success("(, rs274)")
        assert CommentToken.test_success("( , rs274)")
        assert CommentToken.test_success("((, rs274)")
        assert CommentToken.test_success("(Hello , rs274)")
        assert CommentToken.test_success("([Hello], rs274)")
        assert CommentToken.test_success("(Hello world!, rs274)")
        assert CommentToken.test_success("( ( , rs274)")
        assert CommentToken.test_success("( Hello , rs274)")
        assert CommentToken.test_success("( [Hello] , rs274)")
        assert CommentToken.test_success("( Hello world! , rs274)")

        # Fail tests:
        assert not isinstance(CommentToken.match("", 0), CommentToken)
        assert not isinstance(CommentToken.match("x", 0), CommentToken)
        assert not isinstance(CommentToken.match("o", 0), CommentToken)
        assert not isinstance(CommentToken.match("[", 0), CommentToken)
        assert not isinstance(CommentToken.match(")", 0), CommentToken)
        assert not isinstance(CommentToken.match("]", 0), CommentToken)
        assert not isinstance(CommentToken.match("?", 0), CommentToken)

    # CommentToken.test_success():
    @staticmethod
    def test_success(line: str):
        """Verify that line is correctly parsed as a comment."""
        # Tack some different termiators on the line:
        terminators: List[str] = ["", " ", "(", ")"]
        terminator: str
        for terminator in terminators:
            full_line = line + terminator
            token = CommentToken.match(full_line, 0)
            assert isinstance(token, CommentToken), f"'{full_line}' should not have failed"
            assert token.end_index == len(line)
            assert token.comment == line
        return True


# LetterToken:
class LetterToken(Token):
    """Represents a letter tken (e.g. "M6", "G0", "X1.23")."""

    # LetterToken.__init__():
    def __init__(self,
                 end_index: int,
                 letter: str,
                 number: Number,
                 tracing: Optional[str] = None):
        """Initialize a LetterToken.

        Arguments:
            end_index (int): line position where token ends.
            letter (str): The variable letter.
            number (Number): The variable value.

        """
        # Preform any requested *tracing*:
        next_tracing: Optional[str] = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>LetterToken.__init__(*, {end_index}, '{letter}', {number})")

        # Initialize the *letter_token* (i.e. *self*):
        letter_token: LetterToken = self
        super().__init__(end_index, tracing=next_tracing)
        self.letter: str = letter
        self.number: Number = number
        letter_token = letter_token

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>LetterToken.__init__(*, {end_index}, '{letter}', {number})")

    # LetterToken.__str__():
    def __str__(self) -> str:
        """Return LetterToken as a string."""
        # Unpack *token_letter* (i.e. *self*):
        letter_token: LetterToken = self
        letter: str = letter_token.letter
        number: Number = letter_token.number

        # Figure out whether to use an integer of a float to print:
        fractional: float
        whole: float
        fractional, whole = math.modf(number)
        result: str = f"{letter}{int(whole)}" if fractional == 0.0 else f"{letter}{number}"
        return result

    # LetterToken.catagorize():
    def catagorize(self, commands: List[Command], unused_tokens: List[Token]):
        """Sort a LetterToken into a command or an unused token.

        Arguments:
            commands (List[Command]): Commands list to put
                new Command into.
            unused_tokens (List[Token]): Tokens list to put
                non-Command tokens into.

        """
        # Unpack *letter_token* (i.e. *self*):
        letter_token: LetterToken = self
        letter: str = letter_token.letter
        number: Number = letter_token.number

        # Convert 'F', 'G', 'M', 'N', 'S', and 'T' *letter_token* directly into a *command*:
        if letter in "FGMNST":
            name: str = f"{letter}{number}"
            command: Command = Command(name)
            commands.append(command)
        else:
            # Otherwise *letter_token* gets pushed into *unused_tokens*:
            unused_tokens.append(letter_token)

    # LetterToken.match():
    @staticmethod
    def match(line: str, start_index: int) -> "Optional[LetterToken]":
        """Match a LetterToken on a line.

        Arguments:
            line (str): Line to parse token from.
            start_index (int): Line position to start from.
        Returns:
            Optional[LetterToken]: None if now match; othewise
            the newly created LetterToken.

        """
        # print(f"=>token_variable_match(*, '{line}', {start_index})")
        letter: str = ""
        end_index: int = -1
        number_start: int = -1
        number_end: int = -1
        line_size: int = len(line)
        if line_size > 0:
            character: str = line[start_index].upper()
            # print("character='{0}'".format(character))
            if character.isalpha() and character != 'O':
                letter = character
                have_digit: bool = False
                have_decimal_point: bool = False
                index: int
                for index in range(start_index + 1, line_size):
                    # Dispatch on *character*:
                    character = line[index]
                    # print("character='{0}'".format(character))
                    if character.isdigit():
                        # A digit was found:
                        have_digit = True
                        if number_start < 0:
                            number_start = index
                        number_end = index + 1
                    elif character == '.':
                        # Check for decimal point:
                        if have_decimal_point:
                            # Error: We have a duplicate decimal point:
                            break
                        # Start the number if we have not already done so:
                        have_decimal_point = True
                        if number_start < 0:
                            number_start = index
                        number_end = index + 1
                    elif character == '-':
                        # Minus sign must be at beginning of number:
                        if index == start_index + 1:
                            # Minus sign is at beginning so start the number:
                            number_start = index
                            number_end = index + 1
                        else:
                            # Error: Minus sign is not first character in number:
                            break
                    else:
                        # We have found a non digit, so stop scanning:
                        if have_digit:
                            end_index = index
                        break

        # Deal with case where number ends at end of *line*:
        if number_end >= line_size and have_digit:
            end_index = number_end

        # Construct and return *token*:
        letter_token: Optional[LetterToken] = None
        if end_index >= 0:
            number_text = line[number_start:number_end]
            # print(f"number_text='{number_text}'")
            if have_decimal_point:
                number = float(number_text)
            else:
                number = int(number_text)

            # Create the *token* if we have a positive sort_key:
            letter_token = LetterToken(end_index, letter, number)
        # print(f"<=LetterToken.match(*, '{line}', {start_index})=>{letter_token}")
        return letter_token

    # LetterToken.letter_get():
    def letter_get(self) -> str:
        """Return the letter token letter."""
        letter_token: LetterToken = self
        return letter_token.letter

    # LetterToken.number_get():
    def number_get(self) -> Number:
        """Return the letter token number."""
        letter_token: LetterToken = self
        return letter_token.number

    # LetterToken.recatagorize():
    def recatagorize(self, letter_tokens_table: "Dict[str, LetterToken]", errors: List[Error]):
        """Sort token into either *letter_tokens_table* or and error.

        Arguments:
            letter_tokens_table (Dict[str, LetterToken]): The place to
                store unique parameters keyed by parameter letter.
            errors (List[Error]): An error list to append error
                messages to.

        """
        # Grab the *letter* from *letter_token* (i.e. *self*):
        letter_token: LetterToken = self
        letter: str = letter_token.letter_get()

        # Stuff *token* into *tokens_table* (or generate an *error*):
        if letter in letter_tokens_table:
            error: str = f"Parameter '{letter}' occurs more than once in block (i.e. line.)"
            errors.append(error)
        else:
            letter_tokens_table[letter] = letter_token

    # LetterToken.test():
    @staticmethod
    def test():
        """Test LetterToken parsing."""
        # Success tests:
        assert LetterToken.test_success("x1", 1.0)
        assert LetterToken.test_success("x1.", 1.0)
        assert LetterToken.test_success("x.1", 0.1)
        assert LetterToken.test_success("x1.1", 1.1)
        assert LetterToken.test_success("x-1", -1.0)
        assert LetterToken.test_success("x-1.", -1.0)
        assert LetterToken.test_success("x-1.1", -1.1)
        assert LetterToken.test_success("x-.1", -0.1)
        assert LetterToken.test_success("X1", 1.0)
        assert LetterToken.test_success("X1.", 1.0)
        assert LetterToken.test_success("X.1", 0.1)
        assert LetterToken.test_success("X1.1", 1.1)
        assert LetterToken.test_success("X-1", -1.0)
        assert LetterToken.test_success("X-1.", -1.0)
        assert LetterToken.test_success("X-1.1", -1.1)
        assert LetterToken.test_success("X-.1", -0.1)
        variable: str
        for variable in "abcdefghijilmn" + "pqrstuvwxyz":        # No 'o':
            LetterToken.test_success(variable + "1", 1.0)
            LetterToken.test_success(variable.upper() + "1", 1.0)

        # Fail tests:
        assert not isinstance(LetterToken.match("", 0), tuple)
        assert not isinstance(LetterToken.match("?", 0), tuple)
        assert not isinstance(LetterToken.match("x", 0), tuple)
        assert not isinstance(LetterToken.match("X", 0), tuple)
        assert not isinstance(LetterToken.match("xx", 0), tuple)
        assert not isinstance(LetterToken.match("XX", 0), tuple)
        assert not isinstance(LetterToken.match("1", 0), tuple)
        assert not isinstance(LetterToken.match("1X", 0), tuple)

    # LetterToken.test_success():
    @staticmethod
    def test_success(line: str, number: Number):
        """Verify that a line properly parses.

        Arguments:
            line (str): Line to test for matching.
            number (Number): number to match.

        """
        # Tack some different termiators on the line:
        terminators: List[str] = ["", " ", "(", ")", "x"]
        terminator: str
        for terminator in terminators:
            full_line: str = line + terminator
            letter_token: Optional[LetterToken] = LetterToken.match(full_line, 0)
            assert isinstance(letter_token, LetterToken), f"'{full_line}' should not have failed"
            assert letter_token.end_index == len(line)
            assert letter_token.letter == line[0].upper()
            assert letter_token.number == number
        return True


# OLetterToken:
class OLetterToken(Token):
    """Represents a LinuxCNC O code (e.g. "O123 call, ...)."""

    # OLetterToken.__init__():
    def __init__(self,
                 end_index: int,
                 routine_number: int,
                 keyword: str,
                 tracing: Optional[str] = None):
        """Initialize an OLetterToken.

        Arguments:
            end_index (int): The line position where the token ends,
            routine_number (int): The routine number.
            keyword (str): The keyword is one of "call", "sub",
                or "endsub".
            tracing (Optional[str]): None for no tracing; otherwise
                the string to prefix to tracing output.

        """
        # Perfom an requested *tracing*:
        next_tracing: Optional[str] = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{tracing}=>OLetterToken.__init__(*, {end_index}, {routine_number}, '{keyword}')")

        # Initialize the *token_o_letter* (i.e. *self*):
        o_letter_token: OLetterToken = self
        super().__init__(end_index, tracing=next_tracing)
        self.routine_number: int = routine_number
        self.keyword: str = keyword.lower()
        o_letter_token = o_letter_token

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{tracing}<=OLetterToken.__init__(*, {end_index}, {routine_number}, '{keyword}')")

    # OLetterToken.__str__():
    def __str__(self):
        """Return OLetterToken as a string."""
        o_letter_token_letter: OLetterToken = self
        return f"O{o_letter_token_letter.routine_number} {o_letter_token_letter.keyword}"

    # OLetterToken.catagorize():
    def catagorize(self, commands: List[Command], unused_tokens: List[Token]):
        """Sort OLetterToken into unused tokens list."""
        # Currently nobody uses a *oletter_token* (i.e. *self*):
        oletter_token: OLetterToken = self
        unused_tokens.append(oletter_token)

    # OLetterToken.match():
    @staticmethod
    def match(line: str, start_index: int) -> "Optional[OLetterToken]":
        """Match a line to and OLetterToken.

        Arguments:
            line (str): Line text string to parse.
            start_index (int): Line position start at.

        """
        # print("=>OLetterToken.match('{0}', {1})".format(line[start_index:], start_index))
        name: str = ""
        white_space: str = " \t"
        end_index: int = -1
        mode: int = 0
        number_start: int = -1
        number_end: int = -1
        line_size: int = len(line)
        index: int
        for index in range(start_index, line_size):
            character: str = line[index].lower()
            # print("[{0}]:'{1}', mode={2}".format(index, character, mode))
            if mode == 0:
                if character == 'o':
                    mode = 1
                else:
                    break
            elif mode == 1:
                if character.isdigit():
                    if number_start < 0:
                        number_start = index
                    number_end = index + 1
                elif character in white_space:
                    mode = 2
                else:
                    break
            elif mode == 2:
                if character in white_space:
                    pass
                else:
                    for name in ("sub", "endsub", "call"):
                        name_size: int = len(name)
                        name_end_index: int = index + name_size
                        extracted_name: str = line[index:name_end_index].lower()
                        # print("extracted_name='{0}'".format(extracted_name))
                        if name == extracted_name:
                            if name_end_index >= line_size or \
                              name_end_index < line_size and not line[name_end_index].isalpha():
                                # Success: we have a match:
                                # print("total_match")
                                end_index = name_end_index
                            break
                    break

        # If *end_index* is positive, we have successfully matched:
        o_letter_token: Optional[OLetterToken] = None
        if end_index >= 0:
            assert number_start >= 0 and number_end >= 0
            value: int = int(line[number_start:number_end])
            o_letter_token = OLetterToken(end_index, value, name)
        return o_letter_token

    # OLetterToken.number_get():
    def number_get(self) -> Number:
        """Return routine number associated with *OLetterToken*."""
        o_letter_token: OLetterToken = self
        return o_letter_token.routine_number

    # OLetterToken.test():
    @staticmethod
    def test():
        """Test OLetterToken parsing."""
        # Success tests:
        assert OLetterToken.test_success("o0 sub", 0, "sub")
        assert OLetterToken.test_success("o0 call", 0, "call")
        assert OLetterToken.test_success("o0 endsub", 0, "endsub")
        assert OLetterToken.test_success("O0 SUB", 0, "sub")
        assert OLetterToken.test_success("O0 CALL", 0, "call")
        assert OLetterToken.test_success("O0 ENDSUB", 0, "endsub")
        assert OLetterToken.test_success("o1 call", 1, "call")
        assert OLetterToken.test_success("o12 call", 12, "call")
        assert OLetterToken.test_success("o12  call", 12, "call")

        # Failure tests:
        tests: List[str] = ("", "x", "?", "1", "(",
                            "o", "o0", "o0 ", "o0 s", "o0 su", "o0 subx",
                            "o0sub", "o0call", "o0endsub")
        # Failure tests
        test: str
        for test in tests:
            assert not isinstance(OLetterToken.match(test, 0), OLetterToken), \
              "Test '{0}' succeeded when it should not have!".format(test)

    # OLetterToken.test_success():
    @staticmethod
    def test_success(line: str, routine_number: int, keyword: str) -> bool:
        """Test OLetterToken parser for success.

        Arguments:
            line (str): Line containing OToken text.
            routine_number (int): Routine number to match.
            keyword (str): Keyword to match with.

        """
        # Tack some different terminators on the line:
        terminators: List[str] = ["", " ", "(", "["]
        termiantor: str
        for terminator in terminators:
            full_line: str = line + terminator
            o_letter_token: Optional[OLetterToken] = OLetterToken.match(full_line, 0)
            assert isinstance(o_letter_token, OLetterToken), f"'{full_line}' should not have failed"
            assert o_letter_token.end_index == len(line)
            assert o_letter_token.routine_number == routine_number
            assert o_letter_token.keyword == keyword
        return True


# Run this code from the command line:
if __name__ == "__main__":
    main()
