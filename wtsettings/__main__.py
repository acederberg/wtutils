#!/usr/bin/python3.10
"""A tool for formatting the wt configuration file (as yaml) store to json.

I plan to analyze this project using category theory. Though it is mostly useless,
I have found the problem of writing interactive command line tools to be entertaining
thought that this would be useful since writing JSON sucks and I would have to write
a parsing function for removing comments, which would be too easy and convenient.

TL;DR: This is almost entirely pointless beides some fun with esoteric math. Otherwise
It is just a fun tool for adding json snippets from a perminant YAML store.
"""

import json
import re
import shutil
import sys
from os import path
from typing import Dict, List, Optional, Tuple, Union

import yaml
from pydantic import BaseModel, BaseSettings


class Config(BaseSettings):
    """Settings for interactive mode."""

    YAMLConfig: str = path.join(path.dirname(__file__), "settings.yaml")
    JSONConfig: str = "/mnt/c/Users/AdrianCederberg/AppData/Local/Packages/Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe/LocalState"


class WTSettingsJSONSchema(BaseModel):
    """A Json for the windows terminal schemas."""

    def load(cls, config: Optional[Config] = None) -> "WTSettingsJSONSchema":

        filepath = config.JSONConfig
        with open(filepath, "r") as file:
            return cls(**yaml.safe_load(file))


class WTSettingsYAMLSchema(BaseModel):
    """How the YAML document should look."""

    # Configuration dependent methods
    @classmethod
    def load(
        cls, config: Optional[Config] = None, confattr: Optional[str] = None
    ) -> "WTSettingsYAMLSchema":

        config = config if config is not None else Config()

        filepath: str
        if confattr is None:
            filepath = config.YAMLConfig
        elif hasattr(config, confattr) and isinstance(getattr(config, confattr), str):
            filepath = getattr(config, confattr)
        else:
            raise Exception(
                f"confattr = `{confattr}` is not an attribute of `Config` or it not of type `str`."
            )

        assert filepath is not None, "Local 'filepath' must be defined."

        with open(filepath, "r") as file:
            return cls(**yaml.safe_load(file))

    class Action(BaseModel):

        keys: str
        command: Union[str, Dict]

    actions: Dict[str, List[Action]]


class Main:

    config: Config = Config()
    __yes__ = (
        re.compile("Yes", re.IGNORECASE),
        re.compile("Y"),
    )
    __options__ = (
        "Print a set of keybindings as JSON.",
        "Print all keybindings as JSON.",
        "Rerender wt settings from the given actions.",
        "Print a profile as json.",
    )

    # Input methods
    @classmethod
    def input_yes(cls, prompt: str) -> bool:
        """Check that response matches any of the yes options."""

        ans: str = input(prompt)
        return any(regexp.match(ans) is not None for regexp in cls.__yes__)

    @classmethod
    def input_int(cls, n) -> int:
        """"""

        input_: int
        try:
            input_ = int(input())
        except:
            print("That's not an integer. Try again:", end=" ")
            return -1

        if not (0 <= input_ <= n):
            print(
                f"That's not a valid input. Should be positive and less than {n+1}. Try again:",
                end=" ",
            )
            return -1

        return input_

    @classmethod
    def _input_enumerated(cls, n: int, options_: Dict[int, str]) -> str:
        """Helper for :meth:``input_enumerated``.

        Catches ``int`` casting errors, tells the user that their input was not an integer
        or that the integer is outside of the range specified by ``n``.
        :param n: Max length to validate against. Minumum is hardcoded to zero.
        :returns: The interger input.
        """

        input_ = cls.input_int(n)
        return input_, options_[input_] if input_ > -1 else ""

    @classmethod
    def input_enumerated(cls, prompt: str, options: Tuple[str, ...]) -> str:
        """List some options, get a valid response.

        :param prompt: The propmt for the response.
        :param options: The list of items from which a user will select.
        :returns: The index of the answer and the value contained at that index.
        """

        # Verification and prompt.
        n = len(options)
        print(len(options))
        assert n > 0, "Insufficient options parameter. Iterable must not be falsy."

        options_: Dict[int, str] = {
            k: option for k, option in zip(range(0, len(options)), options)
        }
        print(prompt)
        print("\n".join(f"{k}. {option}" for k, option in options_.items()) + "\n")

        # Get the response as a tuple of the selected index
        ans: Tuple[int, str] = next(
            (
                item
                for item in (cls._input_enumerated(n, options_) for _ in range(0, 3))
                if item[0] > -1
            ),
            (-1, ""),  # ew
        )

        if ans[0] == -1:
            print("Failed to collect input. Exiting.")
            sys.exit(1)

        return ans

    @classmethod
    def handle_subsection(
        cls, wtsettings: WTSettingsYAMLSchema, render_all: bool = False
    ) -> None:
        """Handle calling a subsection. This should represent the call signature for
        first level handler.

        :param wtsettings: configuration to read from.
        :returns: None.
        """

        termsize = shutil.get_terminal_size()
        delim = termsize.columns * "="

        print("\nInput the level of indent you want: ", end="")
        indent = cls.input_int(2) or None

        # Print everything altogether and exit.
        if render_all:
            print(delim)
            print(
                json.dumps(
                    tuple(
                        item.dict()
                        for subsection in wtsettings.actions.values()
                        for item in subsection
                    ),
                    indent=indent,
                )
            )
            print(delim)
            sys.exit(0)

        # Print some subsection in particular.
        subsection_name: str
        _, subsection_name = cls.input_enumerated(
            "Choose a subsection to use: ", wtsettings.actions
        )

        print(delim)
        print(
            json.dumps(
                tuple(item.dict() for item in wtsettings.actions[subsection_name]),
                indent=indent,
            )
        )
        print(delim)

        # Exit successfully.
        sys.exit(0)

    def handle_rerender_actions(cls, wtsettings: WTSettingsYAMLSchema) -> None:
        """ """

        print("Incomplete.")

        sys.exit(0)

    @classmethod
    def invoke(cls, config: Optional[Config] = None):

        # Present options to the user. Ignore option value and maintain the option index.
        option_index: int
        option_index, _ = cls.input_enumerated(
            "What would you like to do?", cls.__options__
        )

        # Call the script associated with the option.
        wtsettings: WTSettingsYAMLSchema = WTSettingsYAMLSchema.load(config=config)
        match option_index:
            case 0:
                cls.handle_subsection(wtsettings)
            case 1:
                cls.handle_subsection(wtsettings, render_all=True)
            case _:
                print("Undefined option.")


def main():
    return Main.invoke()


if __name__ == "__main__":
    Main.main()
