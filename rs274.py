#!/usr/bin/env python3
# <---------------------------------------- 100 characters --------------------------------------> #

import sys
import math
import os

# Import some types for type hints:
from typing import Callable, Dict, List, Tuple, Union
Number = Union[float, int]
NullStr = Union[None, str]
Error = str

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


# Forward class declartions that will be overridden further below:
class BracketToken:
    """Forward definition of BracketToken class."""

    def __init__(self):
        """Bogus __init__ method."""
        assert False, "Forward class definition accidentally used."


class CommentToken:
    """Forward definition of CommentToken class."""

    def __init__(self):
        """Bogus __init__ method."""
        assert False, "Forward class definition accidentally used."


class Command:
    """Forward definition of Command class."""

    def __init__(self):
        """Bogus __init__ method."""
        assert False, "Forward class definition accidentally used."


class Group:
    """Forward definition of Group class."""

    def __init__(self):
        """Bogus __init__ method."""
        assert False, "Forward class definition accidentally used."


class LetterToken:
    """Forward definition of LetterToken class."""

    def __init__(self):
        """Bogus __init__ method."""
        assert False, "Forward class definition accidentally used."


class RS274:
    """Forward definition of RS274 class."""

    def __init__(self):
        """Bogus __init__ method."""
        assert False, "Forward class definition accidentally used."


class OLetterToken:
    """Forward definition of OLetterToken class."""

    def __init__(self):
        """Bogus __init__ method."""
        assert False, "Forward class definition accidentally used."


class Template:
    """Forward definition of Template class."""

    def __init__(self):
        """Bogus __init__ method."""
        assert False, "Forward class definition accidentally used."


class Token:
    """Forward definition of Token class."""

    def __init__(self):
        """Bogus __init__ method."""
        assert False, "Forward class definition accidentally used."


# Command:
class Command:
    """Alternative Command class implementation.

    This is an alternative implementation of the the Command class
    for FreeCAD for use when the rs274 module is being used outside
    of FreeCAD.  This class typically represents a single executable
    G/M code with parameters.  It can also represent comments.
    """

    # Command.__init__():
    def __init__(self: Command, name: str, parameters: Union[Dict[str, Number], None] = None):
        """Initialize a *Command* with a name and optional parameters.

        Arguments:
            name (str): The name of the command (e.g. "G0", "M3", etc.)
                A comment is entered as "( comment text )" for the name.
            parameters (dict):  A dictionary that contains the paramter
                values.  Example: "G0 X1.2 Y3.4" would have a parameter
                dictionary of {'X':1.2, 'Y':3.4}.

        """
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(parameters, dict) or parameters is None

        # Create an empty *parameters* dictionary if needed:
        if parameters is None:
            parameters: Dict[str, Number] = dict()

        # Stuff arguments into *command* (i.e. *self*):
        command: Command = self
        command.Name = name
        command.Parameters = parameters

    # Command.__str__():
    def __str__(self: Command) -> str:
        """Return a string reprentation of a *Command*."""
        # Grab some values from *command* (i.e. *self*):
        command: Command = self
        name: str = command.Name
        parameters: Dict[str, Number] = command.Parameters

        # Create a sorted list of *parameters_strings*:
        parameters_strings: List[str] = list()
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
    def __init__(self: Group, rs274: RS274, short_name: str, title: str):
        """Initialize the a Group object.

        Arguments:
            rs274 (RS274): The RS274 object that contains the master
                group tables.
            short_name (str): The short group name.  Usually the first
                 G/M code of the group (e.g. "G0", "M3", etc.)
            title (str): A descriptive title for group
                (e.g. "Motion Control")

        """
        # Verify argument types:
        assert isinstance(rs274, RS274)
        assert isinstance(short_name, str)
        assert isinstance(title, str)

        # Stuff arguments into *group* (i.e. *self*):
        group: Group = self
        group.templates = dict()
        group.title = title
        group.rs274 = rs274
        group.short_name = short_name
        group.key = -1

    # Group.g_code():
    def g_code(self: Group, name: str, parameters: str, title: str):
        """Create an named G code Template with parameters and title.

        Arguments:
            name (str): The G-code name as a string of the form "G#"
                where "#" is a number.
            parameters (str): The list of parameters letters (e. g.
                "ABCXYZ".
            title (str): A short description of the G-code does.

        """
        # Verify argument types:
        assert isinstance(name, str) and name.startswith('G')
        assert isinstance(parameters, str)
        assert parameters == "" or (parameters.isupper() and parameters.isalpha())
        assert isinstance(title, str)
        try:
            float(name[1:])
        except ValueError:
            assert False, f"'{name[1:]}' is not a number"

        # Create *g_code_template and register it with *group* (i.e. *self*):
        g_code_template = Template(name, parameters, title)
        group: Group = self
        group.template_register(g_code_template)

    # Group.m_code():
    def m_code(self: Group, name: str, parameters: str, title: str):
        """Create a named M code Template with parameters and title.

        Arguments:
            name (str): The M-code as a string of the form "M#"
                where "#" is a number.
            parameters (str): The list of parameter letters.
            title (str): A short description of the M-code does.

        """
        # Verify argument types:
        assert isinstance(name, str) and name.startswith('M')
        assert isinstance(parameters, str)
        assert parameters == "" or (parameters.isupper() and parameters.isalpha())
        assert isinstance(title, str)
        try:
            float(name[1:])
        except ValueError:
            assert False, f"'{name[1:]}' is not a number"

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
    def letter_code(self: Group, letter: str, title: str):
        """Create a letter code Template with a title.

        Arguments:
            letter (str): The letter code letter (e.g. 'T', 'F', ...)
            title (str): A short description of the letter code does.

        """
        # Verify argument types:
        assert isinstance(letter, str)
        assert len(letter) == 1 and letter.isalpha() and letter.isupper()
        assert isinstance(title, str)

        group: Group = self
        letter_template: Template = Template(letter, "", title)
        group.template_register(letter_template)

    # Group.template_register():
    def template_register(self: Group, template: Template):
        """Register a new template with with group.

        Arguments:
            template (Template): The template to register with group.

        """
        # Verify argument types:
        assert isinstance(template, Template)

        # Grab some values from *group* (i.e. *self*) and *rs274*:
        group: Group = self
        group_templates: Dict[str, Template] = group.templates
        rs274: RS274 = group.rs274
        parameter_letters: Dict[str, Token] = rs274.parameter_letters
        templates_table: Dict[str, Template] = rs274.templates_table
        groups_table: Dict[str, Group] = rs274.groups_table

        # Make sure that *name* is not duplicated in the global *templates_table*:
        name: str = template.name
        assert name not in templates_table, f"Template '{name}' already in global templates table.'"
        templates_table[name] = template
        groups_table[name] = group

        parameters: Dict[str, Number] = template.parameters
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
    def __init__(self: RS274):
        """Initialize the RS274 object."""
        # Load some values into *rs274* (i.e. *self*):
        rs274 = self
        rs274.comment_group = None        # *Group* for comments (e.g. "( ... )")
        rs274.group_table = dict()        # Command name (e.g. "G0") to associated *Group*"
        rs274.groups_list = list()        # *Group*'s list in execution order
        rs274.groups_list_keyed = False   # *True* if all groups assigned a sort key
        rs274.groups_table = dict()       # *Group*'s table keyed with short name
        rs274.line_number_group = None    # *Group* for N codes.
        rs274.motion_command_name = None  # Name of last motion command (or *None*)
        rs274.motion_group = None         # The motion *Group* is special
        rs274.parameter_letters = dict()  # For testing, collect all template parameters.
        rs274.templates_table = dict()    # Command name (e.g. "G0") to *Template*.
        rs274.variables = dict()          # Unclear if this is needed....
        rs274.white_space = " \t"         # White space characters for tokenizing
        rs274.token_match_routines = (    # The ordered token match routines
            OLetterToken.match,
            LetterToken.match,
            CommentToken.match,
            BracketToken.match
        )

    # RS274.assign_group_keys()
    def assign_group_keys(self: RS274):
        """Ensure that every Group has a valid key."""
        # Do nothing if *groups_list_keyed* is already set.  Any modifications to
        # the grouops of *rs274* (i.e. *self*) will reset *groups_list_keyed*:
        rs274: RS274 = self
        groups_list_keyed = rs274.groups_list_keyed
        if not groups_list_keyed:
            # Sweep through *groups_list* and set the key attribute for each *group*:
            groups_list: List[Group] = rs274.groups_list
            assert isinstance(groups_list, list)
            for index, group in enumerate(groups_list):
                group.key = index

            # Remember that *groups_list_keyed*:
            rs274.groups_list_keyed = True

    # RS274:commands_and_unused_tokens_extract():
    @staticmethod
    def commands_and_unused_tokens_extract(tokens: List[Token],
                                           tracing: NullStr = None) -> (List[Command],
                                                                        List[Error],
                                                                        List[Token]):
        """Split tokens into commands and tokens.

        Arguments:
            tokens (List[Token]): List to tokens to process.
            tracing (NullStr): None for no tracing; otherwise
                the string to prefix to tracing output.

        Returns:
            List[Command]: A list of commands extracted.
            List[Error]: A list of errors encounterd.
            List[Token]: A list of unused Token's.

        """
        # Verify argument types:
        assert isinstance(tokens, list)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            tokens_text: str = RS274.tokens_to_text(tokens)
            print(f"{tracing}=>RS274.commands_and_unused_tokens_extract({tokens_text}, *)")

        # Sweep through *tokens* splitting them into *commands* and *unused_tokens* and
        # collecting *errors* as we go:
        commands: List[Command] = list()
        unused_tokens: List[Token] = list()
        for token in tokens:
            token.catagorize(commands, unused_tokens)

        # Wrap up any requested *tracing* and return both *commands* and *unused_tokens*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            tokens_text: str = RS274.tokens_to_text(tokens)
            commands_text: str = RS274.commands_to_text(commands)
            unused_tokens_text: str = RS274.tokens_to_text(unused_tokens)
            print(f"{tracing}<=RS274.commands_and_unused_tokens_extract({tokens_text}, *)"
                  f"=>{commands_text}, '{unused_tokens_text}'")
        return commands, unused_tokens

    # RS274.commands_to_text():
    @staticmethod
    def commands_to_text(commands: List[Command]) -> str:
        """Return Command's list as a string."""
        # Verify argument types:
        assert isinstance(commands, list)

        return '[' + "; ".join(f"{command}" for command in commands) + ']'

    # RS274.commands_from_tokens():
    def commands_from_tokens(self: RS274,
                             tokens: List[Token],
                             tracing: NullStr = None) -> (List[Command],
                                                          List[Error],
                                                          List[Token],
                                                          str):
        """Return the commands extracted from tokens.

        Arguments:
            tokens (List[Token]): The tokens to process.
            tracing (NullStr): None for no tracing; otherwise
                the string to prefix to tracing output.

        Returns:
            List[Command]: The list of Command's that were extracted.
            List[Error]: The list of Error's detected.
            List[Token]: A list of unused Token's, and
            str: The default motion command name to use afterwards.

        """
        # Verify argument types:
        assert isinstance(tokens, list)
        assert isinstance(tracing, str) or tracing is None
        for token in tokens:
            assert isinstance(token, Token), f"token={token} tokens={tokens}"

        # Perform any requested *tracing*:
        next_tracing: Union[str, None] = None if tracing is None else tracing + " "
        if tracing is not None:
            tokens_text: str = RS274.tokens_to_text(tokens)
            print(f"{tracing}=>RS274.commands_from_tokens('{tokens_text}')")

        # First partition *tokens* into *commands* and *unused_tokens* using *rs274* (i.e. *self*).
        # Tack any *extraction_errors* onto *errors*:
        rs274: RS274 = self
        commands, unused_tokens = \
            RS274.commands_and_unused_tokens_extract(tokens, tracing=next_tracing)

        # Fill up *unused_tokens_table* with each *unused_token* appending any *duplication_errors*
        # onto *errors*:
        errors: List[str] = list()
        unused_tokens_table, duplication_errors = RS274.table_from_tokens(unused_tokens)
        errors.extend(duplication_errors)

        # Flag when two or more *commands* are in the same group:
        conflict_errors, motion_command_name = RS274.group_conflicts_detect(commands)
        errors.extend(conflict_errors)

        # Determine which *commands* want to use which *unused_tokens* using *unused_tokens_table*
        # and *letter_commands_table*.  The updated (and hopefully empty) *unused_tokens* list
        # is returned:
        letter_commands_table: Dict[str, List[Command]] = (
          RS274.letter_commands_table_create(unused_tokens_table, commands, tracing=next_tracing))
        unused_tokens, bind_errors = RS274.tokens_bind_to_commands(letter_commands_table,
                                                                   unused_tokens_table,
                                                                   tracing=next_tracing)
        errors.extend(bind_errors)

        # Perform any requested *tracing*:
        if tracing is not None:
            commands_text: str = RS274.commands_to_text(commands)
            unused_tokens_text: str = RS274.tokens_to_text(unused_tokens)
            print(f"{tracing}commands={commands_text} unused_tokens='{unused_tokens_text}'")

        # Sort the *commands* based on the *Group* key associated with the *command* name:
        groups_table: Dict[str, Group] = rs274.groups_table
        rs274.assign_group_keys()
        commands.sort(key=lambda command:
                      groups_table[command.Name].key if command.Name in groups_table else -1)

        # Wrap up any requested *tracing* and return results:
        if tracing is not None:
            commands_text: str = RS274.commands_to_text(commands)
            tokens_text: str = RS274.tokens_to_text(tokens)
            unused_tokens_text: str = RS274.tokens_to_text(unused_tokens)
            print(f"{tracing}<=RS274.commands_from_tokens('{tokens_text}')"
                  f"=>{commands_text}, *, '{unused_tokens_text}', '{motion_command_name}'")
        return commands, errors, unused_tokens, motion_command_name

    # RS274.content_parse():
    @staticmethod
    def content_parse(content: str, tracing: NullStr = None) -> List[Command]:
        """Parse an RS274 content and return resulting Command's.

        Arguments:
            content (str): The entire file content with lines
                separated by new-line character.
            tracing (NullStr): None for no tracing; otherwise
                the string to prefix to tracing output.

        Returns:
            List[Command]: The list of resulting Command's.

        """
        # Verify argument types:
        assert isinstance(content, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing: Union[str, None] = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>RS274.content_parse(*, '...') ")

        # Split *content* into *blocks* (i.e. lines) and parse them into *commands* that
        # are appended to *command_list*:
        lines = content.split('\n')
        commands_list: List[Command] = list()
        for line_index, line in enumerate(lines):
            # Parse *block* into *commands*:
            next_tracing: Union[str, None] = "" if -1 <= line_index <= -1 else None
            commands, parse_errors = rs274.line_parse(line, tracing=next_tracing)
            commands_list.append(commands)

            # Print out any errors:
            if len(parse_errors) >= 1 or next_tracing is not None:
                print("Line[{0}]='{1}'".format(line_index, line.strip('\r\n')))

                # Print the *errors*:
                for error_index, error in enumerate(parse_errors):
                    print(f" Error[{error_index}]:'{error}'")

                # Dump the *commands*:
                for index, command in enumerate(commands):
                    assert isinstance(command, Command)
                    print(f" Command[{index}]:{command}")

                print("")

        # This arcane command will flatten the *commands_list* into *flattened_commands*:
        flattened_commands: List[Command] = sum(commands_list, [])
        for command in flattened_commands:
            assert isinstance(command, Command)

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
        # Verify argument types:
        assert isinstance(commands, list)
        assert isinstance(file_name, str)

        # Write *commands* out to *file_name*
        with open(file_name, "w") as out_file:
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
        # Verify argument types:
        assert isinstance(commands, list)

        retract_mode: NullStr = None
        updated_commands: List[Command] = list()
        variables: Dict[str, Number] = dict()
        for command in commands:
            # Unpack *command*:
            name: str = command.Name
            parameters: Dict[str, Number] = command.Parameters

            # Update *variables*:
            for key, value in parameters.items():
                if key == 'Z' and name in ("G82", "G83"):
                    if value < variables['Z']:
                        variables['Zdepth'] = value
                    else:
                        variables['Zdepth'] = None
                else:
                    variables[key] = value

            if name in ("G98", "G99"):
                retract_mode = name
                updated_commands.append(command)
            # elif name == "G80":
            #     # variables['Zdepth'] = None
            #     updated_commands.append(command)
            elif name in ("G82", "G83"):
                # Extract the needed values from *parameters* and *varibles*:
                # l = parameters['L'] if 'L' in parameters else (
                #    variables['L'] if 'L' in variables else None)
                p = parameters['P'] if 'P' in parameters else (
                    variables['P'] if 'P' in parameters else None)
                q = parameters['Q'] if 'Q' in parameters else (
                    variables['Q'] if 'Q' in variables else None)
                r = parameters['R'] if 'R' in parameters else (
                    variables['R'] if 'R' in variables else None)
                x = parameters['X'] if 'X' in parameters else variables['X']
                y = parameters['Y'] if 'Y' in parameters else variables['Y']
                z_depth = variables['Zdepth']
                z = variables['Z']

                # Provide *comment_command* to show all of the parameters used for the
                # drilling cycle:
                comment_command = Command(f"( {name} P:{p} Q:{q} R:{r} X:{x} Y:{y} Z:{z}"
                                          f" Zdepth:{z_depth} retract_mode:{retract_mode} )")
                updated_commands.append(comment_command)

                # Rapid (i.e. `G0`) to (*x*, *y*).  We assume that we are already at either
                # *z* height or *r* height from a previous operation:
                updated_commands.append(Command("G0", {'X': x, 'Y': y}))

                # Only drill if *z_depth*, *r* and *z* are rational:
                if z_depth is not None and z_depth < r <= z:
                    # Dispatch on *name*:
                    if name == "G82":
                        # Simple drilling cycle:

                        # Rapid (i.e. `G0`) down to *r* if it makes sense:
                        if r < z:
                            updated_commands.append(Command("G0", {'Z': r}))

                        # Drill (i.e. `G1`) down to *z_depth*:
                        updated_commands.append(Command("G1", {'Z': z_depth}))

                        # Do a dwell if *p* exists and is positive:
                        if p is not None and p > 0.0:
                            updated_commands.append(Command("G4", {'P': p}))

                        # Rapid out of the hole to the correct retract height based
                        # on *retract_mode*:
                        retract_z = r if retract_mode == "G99" else z
                        updated_commands.append(Command("G0", {'Z': retract_z}))
                    elif name == "G83":
                        # Keep pecking down until we get drilled down to *z_depth*:
                        delta = q / 10.0
                        drill_z = z
                        peck_index = 0
                        while drill_z > z_depth:
                            # Rapid (i.e. `G0`) down to *rapid_z*, where *rapid_z* will
                            # be at *r* on the first iteration, and multiples of *q* lower
                            # on subsequent iterations.  The *delta* offset enusures that
                            # the drill bit does not rapid into the hole bottom:
                            rapid_z = r - (peck_index * q) + (0.0 if peck_index == 0 else delta)
                            updated_commands.append(Command("G0", {'Z': rapid_z}))

                            # Drill (i.e. `G1`) down to *drill_z*, where *drill_z* is a
                            # multiple of *q* below *r*.  Never allow *drill_z* to get below
                            # *z_depth*:
                            drill_z = max(r - (peck_index + 1) * q, z_depth)
                            updated_commands.append(Command("G1", {'Z': drill_z}))

                            # Pause at the bottom of the hole if *p* is specified:
                            if p is not None and p > 0:
                                updated_commands.append(Command("G4", {'P': p}))

                            # Retract all the way back to *r*:
                            updated_commands.append(Command("G0", {'Z': r}))

                            # Increment *peck_index* to force further down on the next cycle:
                            peck_index += 1

                        # Retract back up to *z* if we are in `G99` mode:
                        if retract_mode == "G98":
                            updated_commands.append(Command("G0", {'Z': z}))
                else:
                    updated_commands.append(Command(f"( {name} drill operation suppressed because"
                                                    f" Z:{z_depth} < R:{r} <= Zini:{z} false )"))
            elif False and name in ("G0", "G43", "F18.0"):
                x = parameters['X'] if 'X' in parameters else variables['X']
                y = parameters['Y'] if 'Y' in parameters else variables['Y']
                z = parameters['Z'] if 'Z' in parameters else (
                    variables['Z'] if 'Z' in variables else None)
                comment_command = Command(f"( {name} X:{x} Y:{y} Z:{z} )")
                updated_commands.append(comment_command)
                updated_commands.append(command)
            else:
                updated_commands.append(command)

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
        # Verify argument types:
        assert isinstance(commands, list)

        return [command for command in commands if command.Name not in ("G28", "G28.1")]

    # RS274.g91_remove():
    @staticmethod
    def g91_remove(commands: List[Command]):
        """Remove G91 commands from a list of Command's.

        Arguments:
            commands (List[Command]): The list of commands to process.

        Returns:
            List[Command]: The Command's list with G91 removed.

        """
        # Verify argument types:
        assert isinstance(commands, list)

        return [command for command in commands if command.Name not in ("G91",)]

    # RS274.group_conflicts_detect()
    @staticmethod
    def group_conflicts_detect(commands: List[Command]) -> (List[Error], str):
        """Detect group conflicts in a list of Command's.

        Arguments:
            commands (List[Command]):

        Returns:
            List[Error]: List of Error's.
            str: The motion command name (or "" for none).

        """
        # Verify argument types:
        assert isinstance(commands, list)
        for command in commands:
            assert isinstance(command, Command)

        # Grab some values from *rs274* (i.e. *self*):
        motion_group = rs274.motion_group
        assert isinstance(motion_group, Group)
        groups_table = rs274.groups_table

        # Sweep through *commands* using *duplicates_table* to find commands that conflict with
        # one another because they are in the same *Group*:
        duplicates_table = dict()
        errors = list()
        motion_command_name = None
        g80_found = False
        for command in commands:
            # Grab values from *command*:
            name = command.Name
            letter = name[0]
            if name == "G80":
                g80_found = True

            # Find the *group* associated with *command*, or fail trying:
            if name in groups_table:
                group = groups_table[name]
            elif letter in groups_table:
                group = groups_table[letter]
            else:
                # This should not happen:
                error = f"'{name}' has no associated group"
                errors.append(error)
                group = None

            if group is not None:
                # Check for duplicates *group_name* in *duplicates_table*:
                group_name = group.short_name
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

        if g80_found:
            motion_command_name = None

        # Return the resulting *errors* and *motion_command_name*:
        return errors, motion_command_name

    # RS274.group_create():
    def group_create(self: RS274, short_name: str, title: str, before: str = "") -> Group:
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
        # Verify argument types:
        assert isinstance(short_name, str) and short_name != ""
        assert isinstance(title, str)
        assert isinstance(before, str)

        # Grab some values from *rs274* (i.e. *self*):
        rs274: RS274 = self
        groups_table = rs274.groups_table
        groups_list = rs274.groups_list

        # Create the *group*:
        group = Group(rs274, short_name, title)

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
            before_group = groups_table[before]
            before_index = groups_list.index(before_group)
            groups_list.insert(before_index, group)

        # All done.  Return *group*:
        return group

    # RS724.groups_create():
    def groups_create(self: RS274):
        """Create all of the needed groups."""
        # Grab the *groups* object from *rs274* (i.e. *self*):
        rs274 = self

        # The table below is largely derived from section 22 "G Code Order of Execution"
        # from the LinuxCNC G-Code overview documentation
        #
        #    [Order](http://linuxcnc.org/docs/html/gcode/overview.html#_g_code_order_of_execution):
        #
        #  There are some differences (e.g. M5/M9.)

        # O-word commands (optionally followed by a comment but no other words allowed on
        # the same line):

        # The *axes* variable lists all of the axis parameters:
        axes = "XYZABCUVWFS"

        # Line_number:
        line_number_group = rs274.group_create("N", "Line Number")
        line_number_group.letter_code("N", "Line Number")
        rs274.line_number_group = line_number_group

        # Comment (including message)
        comment_group = rs274.group_create("(", "Comment")
        rs274.comment_group = comment_group

        # Set feed rate mode (G93, G94).
        feed_rate_group = rs274.group_create("G93", "Feed Rate")
        feed_rate_group.g_code("G93", "", "Inverse Time Mode")
        feed_rate_group.g_code("G94", "", "Units Per Minute Mode")
        feed_rate_group.g_code("G95", "", "Units Per Revolution Mode")

        # Set feed rate (F).
        feed_group = rs274.group_create("F", "Feed")
        feed_group.letter_code('F', "Set Feed Rate")

        # Set spindle speed (S).
        spindle_speed_group = rs274.group_create("S", "Spindle")
        spindle_speed_group.letter_code('S', "Set Spindle Speed")

        # Select tool (T).
        tool_group = rs274.group_create("T", "Tool")
        tool_group.letter_code('T', "Select Tool")

        # HAL pin I/O (M62-M68).

        # Change tool (M6) and Set Tool Number (M61).
        tool_change_group = rs274.group_create("M6", "Tool Change")
        tool_change_group.m_code("M6", "T", "Tool Change")

        # Spindle on or off (M3, M4, M5).
        spindle_control_group = rs274.group_create("M3", "Spindle Control")
        spindle_control_group.m_code("M3", "S", "Start Spindle Clockwise")
        spindle_control_group.m_code("M4", "S", "Start Spindle Counterclockwise")
        spindle_control_group.m_code("M19", "RQP", "Orient Spindle")
        spindle_control_group.m_code("M96", "DS", "Constant Surface Speed Mode")
        spindle_control_group.m_code("M97", "", "RPM Mode")

        # Save State (M70, M73), Restore State (M72), Invalidate State (M71).

        # Coolant on or off (M7, M8, M9).
        coolant_group = rs274.group_create("M7", "Coolant")
        coolant_group.m_code("M7", "", "Enable Mist Coolant")
        coolant_group.m_code("M8", "", "Enable Flood Coolant")

        # Enable or disable overrides (M48, M49, M50, M51, M52, M53).
        feed_rate_mode_group = rs274.group_create("M48", "Feed Rate Mode")
        feed_rate_mode_group.m_code("M48", "", "Enable Speed/Feed Override")
        feed_rate_mode_group.m_code("M49", "", "Disable Speed/Feed Override")
        feed_rate_mode_group.m_code("M50", "P", "Feed Override Control")
        feed_rate_mode_group.m_code("M51", "P", "Spindle Override Control")
        feed_rate_mode_group.m_code("M52", "P", "Adaptive Feed Control")
        feed_rate_mode_group.m_code("M53", "P", "Feed Stop Control")

        # User-defined Commands (M100-M199).

        # Dwell (G4).
        dwell_group = rs274.group_create("G4", "Dwell")
        dwell_group.g_code("G4", "P", "Dwell")

        # Set active plane (G17, G18, G19).
        plane_selection_group = rs274.group_create("G17", "Plane Selection")
        plane_selection_group.g_code("G17", "", "Use XY Plane")
        plane_selection_group.g_code("G18", "", "Use ZX Plane")
        plane_selection_group.g_code("G19", "", "Use YZ Plane")
        plane_selection_group.g_code("G17.1", "", "Use UV Plane")
        plane_selection_group.g_code("G18.1", "", "Use WU Plane")
        plane_selection_group.g_code("G19.1", "", "Use VW Plane")

        # Set length units (G20, G21).
        units_group = rs274.group_create("G20", "Units")
        units_group.g_code("G20", "", "Use inches for length")
        units_group.g_code("G21", "", "Use millimeters for length")

        # Cutter radius compensation on or off (G40, G41, G42)
        cutter_radius_compensation_group = rs274.group_create("G40",
                                                              "Cutter Radius Compensation Group")
        cutter_radius_compensation_group.g_code("G40", "", "Compensation Off")
        cutter_radius_compensation_group.g_code("G41", "D", "Compensation Left")
        cutter_radius_compensation_group.g_code("G42", "D", "Compensation Right")
        cutter_radius_compensation_group.g_code("G41.1", "DL", "Dynamic Compensation Left")
        cutter_radius_compensation_group.g_code("G42.1", "DL", "Dynamic Compensation Right")

        # Cutter length compensation on or off (G43, G49)
        tool_length_offset_group = rs274.group_create("G43", "Tool Offset Length")
        tool_length_offset_group.g_code("G43", "H", "Tool Length Offset")
        tool_length_offset_group.g_code("G43.1", axes, "Dynamic Tool Length Offset")
        tool_length_offset_group.g_code("G43.2", "H", "Apply Additional Tool Length Offset")
        tool_length_offset_group.g_code("G49", "", "Cancel Tool Length Compensation")

        # Coordinate system selection (G54, G55, G56, G57, G58, G59, G59.1, G59.2, G59.3).
        select_coordinate_system_group = rs274.group_create("G54", "Select Machine Coordinates")
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
        path_control_group = rs274.group_create("G61", "Path Control")
        path_control_group.g_code("G61", "", "Exact Path Mode Collinear Allowed")
        path_control_group.g_code("G61.1", "", "Exact Path Mode No Collinear")
        path_control_group.g_code("G64", "", "Path Blending")

        # Set distance mode (G90, G91).
        distance_mode_group = rs274.group_create("G90", "Distance Mode")
        distance_mode_group.g_code("G90", "", "Absolute Distance Mode")
        distance_mode_group.g_code("G91", "", "Incremental Distance Mode")
        distance_mode_group.g_code("G90.1", "", "Absolute Arc Distance Mode")
        distance_mode_group.g_code("G91.1", "", "Incremental Arc Distance Mode")

        # Set retract mode (G98, G99).
        retract_mode_group = rs274.group_create("G98", "Retract Mode")
        retract_mode_group.g_code("G98", "", "Retract to Start")
        retract_mode_group.g_code("G99", "", "Retract to R")

        # Go to reference location (G28, G30) or change coordinate system data (G10) or
        # set axis offsets (G92, G92.1, G92.2, G94).
        # Reference Motion Mode:
        reference_motion_group = rs274.group_create("G28", "Reference Motion")
        reference_motion_group.g_code("G28", axes, "Go/Set Position")
        reference_motion_group.g_code("G28.1", axes, "Go/Set Position")
        reference_motion_group.g_code("G30", axes, "Go/Set Position")
        reference_motion_group.g_code("G30.1", axes, "Go/Set Position")
        reference_motion_group.g_code("G92", "", "Reset Offsets")
        reference_motion_group.g_code("G92.1", "", "Reset Offsets")
        reference_motion_group.g_code("G92.2", "", "Reset Offsets")

        # Perform motion (G0 to G3, G33, G38.n, G73, G76, G80 to G89),
        # as modified (possibly) by G53:
        motion_group = rs274.group_create("G0", "Motion")
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
        canned_cycles_group = rs274.group_create("G80", "Canned Cycles")
        canned_cycles_group.g_code("G80", "", "Cancel Canned Cycle")

        # Spindle/Coolant stopping:
        spindle_coolant_stopping_group = rs274.group_create("M5", "Spinde/Collant Stopping")
        spindle_coolant_stopping_group.m_code("M5", "", "Stop Spindle")
        spindle_coolant_stopping_group.m_code("M9", "", "Stop Coolant")

        # Stop (M0, M1, M2, M30, M60).
        stopping_group = rs274.group_create("M0", "Machine Stopping and/or Pausing")
        stopping_group.m_code("M0", "", "Program Pause")
        stopping_group.m_code("M1", "", "Program End")
        stopping_group.m_code("M2", "", "Program Pause")
        stopping_group.m_code("M30", "", "Change Pallet and Program End")
        stopping_group.m_code("M60", "", "Program Change Pallet Pause")

    # RS274.group_show():
    @staticmethod
    def groups_show(groups: List[Group], label: str):
        """Print out a labled list of Group's for debugging."""
        assert isinstance(groups, list)
        assert isinstance(label, str)
        print(label)
        for index, group in enumerate(groups):
            assert isinstance(group, Group)
            print("[{0}]:{1}".format(index, [code.key for code in group.codes]))

    # RS274.letter_commands_table_create():
    @staticmethod
    def letter_commands_table_create(unused_tokens_table: Dict[str, LetterToken],
                                     commands: List[Command],
                                     tracing: NullStr = None) -> Dict[str, List[Command]]:
        """Return a table used for token to command binding.

        Arguments:
            unused_tokens_table (Dict[str, LetterToken]): A table of
                tokens keyed by the token letter
                (e.g key=letter_token.letter).
            commands (List[Command]): A list of commands to bind to the
                tokens.
            tracing (NullStr): None for no tracing; otherwise
                the string to prefix to tracing output.

        Returns:
            Dict[str, List[Command]]: A table keyed by parameter letter
                lists the Command(s) that need to use parameter letter.

        """
        # Verify argument types:
        assert isinstance(unused_tokens_table, dict)
        assert isinstance(commands, list)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        if tracing is not None:
            unused_tokens_text = RS274.tokens_to_text(list(unused_tokens_table.values()))
            commands_text = RS274.commands_to_text(commands)
            print(f"{tracing}=>RS274.letter_commands_table_create("
                  f"{unused_tokens_text}, {commands_text})")

        # Start filling up *letter_template_table*:
        letter_commands_table = dict()
        templates_table = rs274.templates_table
        for letter_index, letter in enumerate(unused_tokens_table.keys()):
            # Perform any requested *tracing*:
            assert isinstance(letter, str)
            assert isinstance(letter_index, int)
            # if tracing is not None:
            #     print(f"{tracing}Letter[{letter_index}]:'{letter}'")

            # Now sweep through *commands* trying to figure out which command wants which
            # unused token:
            for command_index, command in enumerate(commands):
                # Unpack *command*:
                assert isinstance(command, Command)
                assert isinstance(command_index, int)
                name = command.Name
                # if tracing is not None:
                #     print(f"{tracing} Command[{command_index}]:{command}")

                # Look up the *template* from *templates_table*
                if name in templates_table:
                    template = templates_table[name]
                    # if tracing is not None:
                    #     print(f"{tracing}  Template[{command_index}]:{template}")

                    # Register *command* is needing *template_letter* from *template*:
                    for template_index, template_letter in enumerate(template.parameters.keys()):
                        assert isinstance(template_index, int)
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
            pairs = list()
            for letter, sub_commands in letter_commands_table.items():
                sub_commands_text = RS274.commands_to_text(sub_commands)
                pairs.append(f"'{letter}': {sub_commands_text}")
            pairs_text = '{' + ', '.join(pairs) + '}'
            print(f"{tracing}<=RS274.letter_commands_table_create("
                  f"{unused_tokens_text}, {commands_text})=>{pairs_text}")

        return letter_commands_table

    # RS274:line_parse():
    def line_parse(self: RS274, line: str,
                   tracing: NullStr = None) -> (List[Command], List[Error]):
        """Parse one line of CNC code into a list of commands.

        Args:
            line (str): The line of CNC code to parse. There
                be no trailing new-line character.
            tracing: (NullStr): Either *None* for no tracing, or a
                tracing indentation string (usually a string of spaces.)

        Returns:
            commands (List[Command]): A list of *Command*'s for each
                CNC command in *block*.  This returned list is empty if there
                are no commands.
            errors (List[str]): A list of error strings.

        """
        # Verify argument types:
        assert isinstance(line, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing: NullStr = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>RS274.line_parse('{line}', *)")

        # Start with *final_codes* set to *None*.  Only override *final_commands* with a list
        # of *Command*'s if there are no errors and no unused tokens:
        errors: List[Error] = list()
        final_commands: List[Command] = None

        # Grab *motion_command_name* from *rs274*; it will be stuffed back into *rs274* later:
        rs274 = self
        motion_command_name: str = rs274.motion_command_name
        assert isinstance(motion_command_name, str) or motion_command_name is None
        if tracing is not None:
            print(f"{tracing}before: motion_command_name='{motion_command_name}'")

        # Start by tokenizing the *block* (i.e. a line of G-code) into *tokens*:
        tokens, tokenize_errors = rs274.line_tokenize(line)
        errors.extend(tokenize_errors)

        for token in tokens:
            if isinstance(token, LetterToken) and token.letter == 'G' and token.number == 80:
                motion_command_name = "G0"
                break

        # We only continue with the parsing if there were no *errors* tokenizing *block*:
        if len(errors) >= 1:
            # We did not get very far, so just set *final_codes* to an empty list return it:
            final_commands: List[Command] = list()
        else:
            # Now we try to parse *tokens* into a list of *final_codes*.  First we try it
            # without adding on a "sticky" motion G command.  If that fails, we try to add
            # on a "sticky" motion G command, and see if the fixes things up:

            # Do the first attempt at parsing tokens into *final_commands*:
            commands1, errors1, unused_tokens1, motion_command_name1 = \
              rs274.commands_from_tokens(tokens, tracing=next_tracing)
            assert isinstance(motion_command_name1, str) or motion_command_name1 is None

            # If there are no errors and no unused tokens, we have succeeded:
            if not errors1 and not unused_tokens1:
                # We have have succeeded.  Update both *final_codes* and *motion_command_name*:
                final_commands: List[Command] = commands1
                if motion_command_name1 is not None:
                    # print(f"setting motion_command_name={motion_command_name}")
                    motion_command_name = motion_command_name1
                if tracing is not None:
                    print(f"{tracing}motion_command_name='{motion_command_name}'")

            # If the first parse of *tokens* has some left over tokens *AND* there was no
            # motion token found (e.g. G0, G3, G82, etc.)  It makes sense to try again by
            # attempting to fix the problems by adding a *Token* based on *motion_command_name*
            # into the *tokens* mix:
            no_final_commands = final_commands is None
            if tracing is not None:
                print(f"{tracing}no_final_commands={no_final_commands}")
                unused_tokens1_text = RS274.tokens_to_text(unused_tokens1)
                print(f"{tracing}unused_tokens1='{unused_tokens1_text}'")
                print(f"motion_command_name='{motion_command_name}'")
                print(f"motion_command_name1='{motion_command_name1}'")
            if (no_final_commands and (len(unused_tokens1) >= 1 and
                                       motion_command_name is not None and
                                       motion_command_name1 is None)):

                # If we have a *motion_command_name*, create a *letter_token* and tack it onto
                # *tokens*:
                assert isinstance(motion_command_name, str) and len(motion_command_name) >= 2
                letter: str = motion_command_name[0]
                assert letter in "G"
                number_text: str = motion_command_name[1:]
                number: Number = float(number_text) if '.' in number_text else int(number_text)
                letter_token: Token = LetterToken(0, letter, number)
                tokens.append(letter_token)

                # Tack *motion_name* (as a *Token*) onto *tokens* and try again:
                commands2, errors2, unused_tokens2, motion_command_name2 = \
                    rs274.commands_from_tokens(tokens, tracing=next_tracing)
                assert isinstance(motion_command_name2, str) or motion_command_name2 is None

                # for index, command in enumerate(commands1):
                #     print(f" commands2[{index}]:{command}")
                # for index, unused_token in enumerate(unused_tokens1):
                #     print(f" unused_tokens2[{index}']:{unused_token}")

                # If there are no errors and no unused tokens, we have succeeded:
                if not errors2 and not unused_tokens2:
                    # We have succeeded by adding *motion_command_name* to *tokens*:
                    final_commands = commands2
                    if motion_command_name2 is not None:
                        motion_command_name = motion_command_name2

                # print(f"len(errors2)={len(errors2)}")
                # print(f"len(unused_tokens2)={len(unused_tokens2)}")
                # print(f"motion_token2={motion_token2}")
                # final_commands_text = ("None" if final_commands is None
                #                        else f"{len(final_commands)}"
                # print(f"final_commands={final_commands_text}")

            # Use *codes1*, *errors1*, and *motion_command_name* if we did not successfully
            # generate *final_commands* without errors and unused tokens:
            if final_commands is None:
                final_commands = commands1
                errors.extend(errors1)
                if len(unused_tokens1) >= 1:
                    unused_text: str = RS274.tokens_to_text(unused_tokens1)
                    unused_tokens_error: str = f"'{unused_text}' is/are unused"
                    errors.append(unused_tokens_error)
                if motion_command_name is not None:
                    motion_command_name = motion_command_name1

        # Now we can stuff *model_motion_name* back into *rs274*:
        rs274.motion_command_name = motion_command_name
        if tracing is not None:
            print(f"{tracing}after: motion_command_name='{motion_command_name}'")

        # Wrap up any requested *tracing* and return *final_commands*:
        if tracing is not None:
            final_commands_text = RS274.commands_to_text(final_commands)
            print(f"{tracing}<=RS274.line_parse('{line}', *)=>{final_commands_text}")
        return final_commands, errors

    # RS274:line_tokenize():
    def line_tokenize(self: RS274, line: str) -> (List[Token], List[Error]):
        """Convert line of G code into Token's.

        Arguments:
            line (str): A line of G-code with no new-line character.

        Returns:
            List[Token]: A list of parsed tokens.
            List[Error]: A list of token parsing errors.

        """
        # Verify argument types:
        assert isinstance(line, str)

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
                token: Union[Token, None] = None
                for match_routine in match_routines:
                    token: Token = match_routine(line, index)
                    if isinstance(token, Token):
                        # We have a match, so remember *token*:
                        matched = True
                        tokens.append(token)
                        # Update *index* to point to the next token:
                        index = token.end_index
                        break
                if not matched:
                    remaining: str = line[index:]
                    error = f"Can not parse '{remaining}'"
                    errors.append(error)
                    break

        return tokens, errors

    # RS274.n_remove():
    @staticmethod
    def n_remove(commands: List[Command]) -> List[Command]:
        """Return a copy of commands with N codes removed."""
        # Verify arguments:
        assert isinstance(commands, list)

        return [command for command in commands if command.Name[0] != 'N']

    # RS274.table_from_tokens():
    @staticmethod
    def table_from_tokens(tokens: List[Token]) -> (Dict[str, Token], List[Error]):
        """Convert tokens into a dict with list duplicate errors list.

        Arguments:
            tokens (List[Token]): The list of tokens to process.

        Returns:
            Dict[str, Token]: The token dictionary keyed on token name/letter.
            List[Error]: List of duplicate errors.

        """
        # Verify argument types:
        assert isinstance(tokens, list)
        for token in tokens:
            assert isinstance(token, LetterToken)

        # Fill up *tokens_table* with each *token* checking for duplicates:
        errors = list()
        tokens_table = dict()
        for token in tokens:
            # Unpack *token*:
            letter = token.letter

            # Stuff *token* into *tokens_table* (or generate an *error*):
            if letter in tokens_table:
                error = f"Parameter '{letter}' occurs more than once in block (i.e. line.)"
                errors.append(error)
            else:
                tokens_table[letter] = token

        # Return *tokens_table* and *errors*:
        return tokens_table, errors

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
                                unused_tokens_table: Dict[str, Token],
                                tracing: NullStr = None) -> (List[Token], List[Error]):
        """Merge unused tokens into pending commands.

        Arguments:
            letter_commands_table (Dict[str, List[Command]): A dict
                of parameters keyed by parameter letter with values
                list the Command's that use the parameter letter.
            unused_tokens_table (Dict[str, Token)]: A dict of tokens
                keyed by parameter letter that are available for
                binding to commands.
            tracing

        """
        # Verify argument types:
        assert isinstance(letter_commands_table, dict)
        assert isinstance(unused_tokens_table, dict)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        if tracing is not None:
            letters_text = " ".join([f"{letter}" for letter in letter_commands_table.keys()])
            unused_tokens_text = RS274.tokens_to_text(list(unused_tokens_table.values()))
            print(f"{tracing}=>RS274.tokens_bind_to_commands("
                  f"'{letters_text}', '{unused_tokens_text}')")

        # Now sweep through *letter_commands_table* looking for *errors* and attaching
        # each appropriate *token* to a *command* (thereby making them used tokens):
        errors = list()
        for letter, letter_commands in letter_commands_table.items():
            # Each *letter* in *letter_commands_table has an associated list of *Command*'s:
            assert isinstance(letter, str)
            assert isinstance(letter_commands, list)

            # Dispatch on *letter_commands_size*:
            letter_commands_size = len(letter_commands)
            if letter_commands_size == 0:
                # *letter* is unused, so there is nothing to do:
                pass
            elif letter_commands_size == 1:
                # Remove the *token* associated with *letter* from *unused_tokens_table*:
                token = unused_tokens_table[letter]
                del unused_tokens_table[letter]

                # Take the *token* value and put it into *command*:
                command = letter_commands[0]
                assert isinstance(command, Command)
                parameters = command.Parameters
                parameters[letter] = token.number
            elif letter_commands_size >= 2:
                # We have a conflict, so we generate an *error*:
                command_names = [command.Name for command in letter_commands]
                conflicting_commands = ", ".join(command_names)
                error = f"Commands '{conflicting_commands}' need to use the '{letter}' parameter"
                errors.append(error)

        # Generate an updated list of *unused_tokens* from what is left in *unused_tokens_table*:
        unused_tokens = list(unused_tokens_table.values())

        # Wrap up any requested *tracing* and return *unused_tokens* list with *errors*:
        if tracing is not None:
            unused_tokens_text = RS274.tokens_to_text(unused_tokens)
            print(f"{tracing}<=RS274.tokens_bind_to_commands(*, *)=>{unused_tokens_text}, *")
        return unused_tokens, errors

    # RS274.tokens_to_text():
    @staticmethod
    def tokens_to_text(tokens):
        """Return turn token list as a string."""
        # Verify argument types:
        assert isinstance(tokens, list)

        return '[' + ", ".join([f"{token}" for token in tokens]) + ']'


class Template:
    """Represents a G/M code that is a member of a Group."""

    # Template.__init__():
    def __init__(self: Template, name: str, parameter_letters: str, title: str):
        """Initialize a template with a name, title and parameters.

        Arguments:
            name (str): The name of the template M/G code (e.g. "G0",
                "M3", etc.)
            parameters_letters (str): A list of parameters that this
                command takes.  Example: The "G0" command can take any
                of axis parameters "ABCUVWXYZ".
            title (str): A description title for documentation purposes.

        """
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(parameter_letters, str)
        assert isinstance(title, str)

        # Create a *parameters* dictionary and fill it in from *parameter_letters*:
        parameters = dict()
        for parameter_letter in parameter_letters:
            parameters[parameter_letter] = 0

        # Stuff arguments into *template* (i.e. *self*):
        template: Template = self
        template.name = name
        template.parameters = parameters
        template.title = title

    # Template.__str__():
    def __str__(self: Template) -> str:
        """Return a string representation of a Template."""
        # Grab some values from *template* (i.e. *self*):
        template: Template = self
        name: str = template.name
        parameters: Dict[str, Number] = template.parameters
        title: str = template.title

        # Create a sorted list of *parameters_strings*:
        parameters_letters = list(parameters.keys())
        parameters_letters.sort()

        # Generate and return the final *result*:
        parameters_letters_text = "".join(parameters_letters)
        result: str = f"{name} '{parameters_letters_text}' '{title}'"
        return result


# Token:
class Token:
    """Represent on token on a G-code line (e.g. "M7", "T1", "X3.1")."""

    # Token.__init__():
    def __init__(self: Token, end_index: int, tracing: NullStr = None):
        """Initialize a Token to have a position.

        Arguments:
            end_index (int) : The position in the line where the
                token ends.
            tracing (NullStr): None for no tracing; otherwise
                the string to prefix to tracing output.

        """
        # Verify argument types:
        assert isinstance(end_index, int) and end_index >= 0
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>Token.__init__(*, {end_index})")

        # Fill in the *token* object (i.e. *self*) from the routine arguments:
        token = self
        token.end_index = end_index

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Token.__init__(*, {end_index})")

    # Token.__str__():
    def __str__(self: Token):
        """Return text string for token."""
        return "?"

    # Token.catagorize():
    def catagorize(self: Token, commands: List[Command], unused_tokens: List[Token]):
        """Place holder routine that fails."""
        # Verify argument types:
        assert isinstance(commands, list)
        assert isinstance(unused_tokens, list)

        # If this routine is called, we have missed writing a *catagorize* method somewhere:
        token = self
        assert False, f"No catagorize() method for {type(token)}"


# BracketToken:
class BracketToken(Token):
    """Represent a NIS RS274 indirect argument (e.g "[123.456]")."""

    # BracketToken.__init__():
    def __init__(self: BracketToken, end_index: int, value: Number, tracing: NullStr = None):
        """Initialize a BracketToken to have a value.

        Arguments:
            end_index (int): The end position of token in the line.
            value (Number): The number value between the brackets.
            tracing (NullStr): None for no tracing; otherwise
                the string to prefix to tracing output.

        """
        # Verify argument types:
        assert isinstance(end_index, int) and end_index >= 0
        assert isinstance(value, (int, float))
        assert isinstance(tracing, str) or tracing is None

        # Perform an requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>BracketToken.__init__(*, {end_index}, {value})")

        # Initialize the *token_bracket* (i.e. *self*):
        token_bracket = self
        super().__init__(end_index, tracing=next_tracing)
        token_bracket.value = value

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>BracketToken.__init__(*, {end_index}, {value})")

    # BracketToken.__str__():
    def __str__(self: BracketToken):
        """Convert BracketToken to human readable string."""
        token_bracket = self
        return "[{0}]".format(token_bracket.value)

    # BracketToken.catagorize():
    def catagorize(self: BracketToken, commands: List[Command], unused_tokens: List[Token]):
        """Catagorize the bracket token into unused tokens."""
        # Verify argument types:
        assert isinstance(commands, list)
        assert isinstance(unused_tokens, list)

        # Currently nobody uses a *bracket_token* (i.e. *self*):
        bracket_token = self
        unused_tokens.append(bracket_token)

    # BracketToken.match():
    @staticmethod
    def match(line: str,
              start_index: int,
              tracing: NullStr = None) -> Union[BracketToken, None]:
        """Parse a BracketToken from line.

        Arguments:
            line (str): The line of G-code to parse from.
            start_index (int): The character position to start at.

        Returns:
            Union[BracketToken, None]: The resulting BracketToken
            or None if no match found.

        """
        # Verify argument types:
        assert isinstance(line, str)
        assert isinstance(start_index, int) and start_index >= 0
        assert isinstance(tracing, str) or tracing is None

        # Perform requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{tracing}=>BracketToken.match('{line}', {start_index}")

        # Set *end_index* to index after the closing square bracket when we have succeeded.
        # If *end_index* is less than zero, we have not successfully matched a bracket token:
        end_index = -1

        # We must start with a '[':
        line_size = len(line)
        if line_size > 0 and line[start_index] == '[':
            white_space = " \t"
            have_decimal_point = False
            have_digit = False
            have_number = False

            # *number_start* and *number_end* point to the character span of the number
            # excluding brackets and white space.  The span is only valid if both are positive:
            number_start = -1
            number_end = -1

            # Sweep across the remainder of *line* starting after the opening '[':
            for index in range(start_index + 1, len(line)):
                # Dispatch on *character*:
                character = line[index]
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
        token = None
        if end_index >= 0:
            token = BracketToken(end_index, float(line[number_start:number_end]))

        # Wrap up any requested *tracing* and return *token*:
        if tracing is not None:
            print("{tracing}<=BracketToken.match('{line}', {start_index2})=>{token}")
        return token

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
        # Verify argument types:
        assert isinstance(line, str)
        assert isinstance(value, float)

        # Tack some different termiators on the end of *block* to test end cases:
        terminators = ("", " ", "[", "]", "x")
        for terminator in terminators:
            # Now verify that *block* is matched and the resulting *token* is correct:
            token = BracketToken.match(line + terminator, 0)
            assert isinstance(token, BracketToken)
            assert token.end_index == len(line)
            assert token.value == value
        return True


# CommentToken:
class CommentToken(Token):
    """Represents an RS274 comment (e.g. '( comment )'."""

    # CommentToken.__init__:
    def __init__(self: CommentToken,
                 end_index: int,
                 is_first: bool,
                 comment: str,
                 tracing: NullStr = None):
        """Initialze a CommentToken.

        Arguments:
            end_index (int): The line position where the token ends.
            is_first (bool): True if at beginning of line.
            comment (str): The actual comment including parenthesis.
            tracing (NullStr): None for no tracing; otherwise
                the string to prefix to tracing output.

        """
        # Verify argument types:
        assert isinstance(end_index, int) and end_index >= 0
        assert isinstance(is_first, bool)
        assert isinstance(comment, str)

        # Preform any requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{tracing}=>CommentToken.__init__(*, {end_index}, {is_first}, '{comment}')")

        # Initialize the *token_comment* (i.e. *self*):
        token_comment = self
        super().__init__(end_index)
        token_comment.is_first = is_first
        token_comment.comment = comment

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{tracing}<=CommentToken.__init__(*, {end_index1}, {is_first}, {comment})")

    # CommentToken.__str__():
    def __str__(self: CommentToken):
        """Return CommentToken as string."""
        token_comment = self
        return token_comment.comment

    # CommentToken.catagorize():
    def catagorize(self: CommentToken, commands: List[Command], unused_tokens: List[Token]):
        """Catagorize a comment token into commands list.

        Arguments:
            commands (List[Command]): Command's list to
                catagorize CommentToken to.
            unused_tokens (List[Tokens]): Unused.

        """
        # Verify argument types:
        assert isinstance(commands, list)
        assert isinstance(unused_tokens, list)

        # Currently nobody uses a *bracket_token* (i.e. *self*):
        comment_token = self
        comment = comment_token.comment
        comment_command = Command(comment)
        commands.append(comment_command)

    # CommentToken.match():
    @staticmethod
    def match(line, start_index):
        """Match an RS274 comment (e.g. '( comment )').

        Arugments:
            line (str): The line to parse comment from.
                start_index (int): The position to start parsing at.

        Returns:
            Union[CommentToken, None]: None if no match found;
                othewise, a new CommentToken.

        """
        # Verify argument types:
        assert isinstance(line, str)
        assert isinstance(start_index, int)
        end_index = -1

        # We most start with a open parenthesis:
        is_first = start_index == 0
        line_size = len(line)
        if line_size > 0 and line[start_index] == '(':
            # Scan looking for the closing parenthesis:
            for index in range(start_index + 1, line_size):
                if line[index] == ')':
                    # We have successfully matched a parenthesis:
                    end_index = index + 1
                    break

        # We have have successfully matached a comment if *end_index* is positive:
        token = None
        if end_index >= 0:
            token = CommentToken(end_index, is_first, line[start_index:end_index])
        # print("token_comment_match(*, '{0}', {1}) => {2}".format(line, start_index, token))
        return token

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
        # Verify argument types:
        assert isinstance(line, str)

        # Tack some different termiators on the line:
        terminators = ("", " ", "(", ")")
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
    def __init__(self: LetterToken,
                 end_index: int,
                 letter: str,
                 number: Number,
                 tracing: NullStr = None):
        """Initialize a LetterToken.

        Arguments:
            end_index (int): line position where token ends.
            letter (str): The variable letter.
            number (Number): The variable value.

        """
        # Verify argument types:
        assert isinstance(end_index, int) and end_index >= 0
        assert (isinstance(letter, str) and
                len(letter) == 1 and letter.isalpha() and letter.isupper())
        assert isinstance(number, (float, int))

        # Preform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>LetterToken.__init__(*, {end_index}, '{letter}', {number})")

        # Initialize the *token_letter* (i.e. *self*):
        token_letter = self
        super().__init__(end_index, tracing=next_tracing)
        token_letter.letter = letter
        token_letter.number = number

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>LetterToken.__init__(*, {end_index}, '{letter}', {number})")

    # LetterToken.__str__():
    def __str__(self: LetterToken) -> str:
        """Return LetterToken as a string."""
        # Unpack *token_letter* (i.e. *self*):
        token_letter = self
        letter = token_letter.letter
        number = token_letter.number

        # Figure out whether to use an integer of a float to print:
        fractional, whole = math.modf(number)
        if fractional == 0.0:
            result = "{0}{1}".format(letter, int(whole))
        else:
            result = "{0}{1}".format(letter, number)
        return result

    # LetterToken.catagorize():
    def catagorize(self: LetterToken, commands: List[Command], unused_tokens: List[Token]):
        """Sort a LetterToken into a command or an unused token.

        Arguments:
            commands (List[Command]): Commands list to put
                new Command into.
            unused_tokens (List[Token]): Tokens list to put
                non-Command tokens into.

        """
        # Verify argument types:
        assert isinstance(commands, list)
        assert isinstance(unused_tokens, list)

        # Unpack *letter_token* (i.e. *self*):
        letter_token = self
        letter = letter_token.letter
        number = letter_token.number

        # Convert 'F', 'G', 'M', 'N', 'S', and 'T' *letter_token* directly into a *command*:
        if letter in "FGMNST":
            name = f"{letter}{number}"
            command = Command(name)
            commands.append(command)
        else:
            # Otherwise *letter_token* gets pushed into *unused_tokens*:
            unused_tokens.append(letter_token)

    # LetterToken.match():
    @staticmethod
    def match(line: str, start_index: int) -> Union[LetterToken, None]:
        """Match a LetterToken on a line.

        Arguments:
            line (str): Line to parse token from.
            start_index (int): Line position to start from.
        Returns:
            Union[LetterToken, None]: None if now match; othewise
            the newly created LetterToken.

        """
        # Verify argument types:
        assert isinstance(line, str)
        assert isinstance(start_index, int)

        # print(f"=>token_variable_match(*, '{line}', {start_index})")
        letter = None
        end_index = -1
        number_start = -1
        number_end = -1
        line_size = len(line)
        if line_size > 0:
            character = line[start_index].upper()
            # print("character='{0}'".format(character))
            if character.isalpha() and character != 'O':
                letter = character
                have_digit = False
                have_decimal_point = False
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
        token = None
        if end_index >= 0:
            number_text = line[number_start:number_end]
            # print(f"number_text='{number_text}'")
            if have_decimal_point:
                number = float(number_text)
            else:
                number = int(number_text)

            # Create the *token* if we have a positive sort_key:
            token = LetterToken(end_index, letter, number)
        # print(f"<=token_variable_match(*, '{line}', {start_index})=>{token}")
        return token

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
        # Verify argument types:
        assert isinstance(line, str)
        assert isinstance(number, (float, int))

        # Tack some different termiators on the line:
        terminators = ("", " ", "(", ")", "x")
        for terminator in terminators:
            full_line = line + terminator
            token = LetterToken.match(full_line, 0)
            assert isinstance(token, LetterToken), f"'{full_line}' should not have failed"
            assert token.end_index == len(line)
            assert token.letter == line[0].upper()
            assert token.number == number
        return True


# OLetterToken:
class OLetterToken(Token):
    """Represents a LinuxCNC O code (e.g. "O123 call, ...)."""

    # OLetterToken.__init__():
    def __init__(self: OLetterToken,
                 end_index: int,
                 routine_number: int,
                 keyword: str,
                 tracing: NullStr = None):
        """Initialize an OLetterToken.

        Arguments:
            end_index (int): The line position where the token ends,
            routine_number (int): The routine number.
            keyword (str): The keyword is one of "call", "sub",
                or "endsub".
            tracing (NullStr): None for no tracing; otherwise
                the string to prefix to tracing output.

        """
        # Verify argument types:
        assert isinstance(end_index, int) and end_index >= 0
        assert isinstance(routine_number, int) and routine_number >= 0
        assert isinstance(keyword, str) and keyword.lower() in ("call", "sub", "endsub")

        # Perfom an requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{tracing}=>OLetterToken.__init__(*, {end_index}, {routine_number}, '{keyword}')")

        # Initialize the *token_o_letter* (i.e. *self*):
        token_o_letter = self
        super().__init__(end_index, tracing=next_tracing)
        token_o_letter.routine_number = routine_number
        token_o_letter.keyword = keyword.lower()

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{tracing}<=OLetterToken.__init__(*, {end_index}, {routine_number}, '{keyword}')")

    # OLetterToken.__str__():
    def __str__(self: OLetterToken):
        """Return OLetterToken as a string."""
        token_letter = self
        return "O{0} {1}".format(token_letter.routine_number, token_letter.keyword)

    # OLetterToken.catagorize():
    def catagorize(self: OLetterToken, commands: List[Command], unused_tokens: List[Token]):
        """Sort OLetterToken into unused tokens list."""
        # Verify argument types:
        assert isinstance(commands, list)
        assert isinstance(unused_tokens, list)

        # Currently nobody uses a *oletter_token* (i.e. *self*):
        oletter_token = self
        unused_tokens.append(oletter_token)

    # OLetterToken.match():
    @staticmethod
    def match(line: str, start_index: int):
        """Match a line to and OLetterToken.

        Arguments:
            line (str): Line text string to parse.
            start_index (int): Line position start at.

        """
        # Verify argument types:
        assert isinstance(line, str)
        assert isinstance(start_index, int)
        # print("=>OLetterToken.match('{0}', {1})".format(line[start_index:], start_index))
        name = "None"
        white_space = " \t"
        end_index = -1
        mode = 0
        number_start = -1
        number_end = -1
        line_size = len(line)
        for index in range(start_index, line_size):
            character = line[index].lower()
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
                        name_size = len(name)
                        name_end_index = index + name_size
                        extracted_name = line[index:name_end_index].lower()
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
        token = None
        if end_index >= 0:
            assert number_start >= 0 and number_end >= 0
            assert isinstance(name, str)
            value = int(line[number_start:number_end])
            token = OLetterToken(end_index, value, name)
        return token

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
        tests = ("", "x", "?", "1", "(",
                 "o", "o0", "o0 ", "o0 s", "o0 su", "o0 subx",
                 "o0sub", "o0call", "o0endsub")
        # Failure tests
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
        # Verify argument types:
        assert isinstance(line, str)
        assert isinstance(routine_number, int)
        assert isinstance(keyword, str)

        # Tack some different terminators on the line:
        terminators = ("", " ", "(", "[")
        for terminator in terminators:
            full_line = line + terminator
            token = OLetterToken.match(full_line, 0)
            assert isinstance(token, OLetterToken), f"'{full_line}' should not have failed"
            assert token.end_index == len(line)
            assert token.routine_number == routine_number
            assert token.keyword == keyword
        return True


if __name__ == "__main__":
    rs274 = RS274()
    rs274.groups_create()
    rs274.token_match_tests()

    file_names = sys.argv[1:]

    print("Final commands list:")
    for file_name in file_names:
        print("file_name='{0}'".format(file_name))
        with open(file_name, "r") as in_file:
            content = in_file.read()
            commands = RS274.content_parse(content)
            commands = RS274.n_remove(commands)
            commands = RS274.g28_remove(commands)
            commands = RS274.g91_remove(commands)
            commands = RS274.drill_cycles_replace(commands)
            rs274.commands_write(commands, os.path.join("/tmp", file_name))
            # commands = rs274.g83.replace(commands)
            # for command_index, command in enumerate(commands):
            #        print(" Commandx[{0}]: {1}".format(command_index, command))
        print("")
