from os import path
from typing import Dict, List, Optional, Tuple, Union

import yaml
from pydantic import BaseModel, BaseSettings


class Config(BaseSettings):
    """Settings for interactive mode."""

    YAMLConfig: str = path.join(path.dirname(__file__), ".wtsettings")
    JSONConfig: str = "/mnt/c/Users/AdrianCederberg/AppData/Local/Packages/Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe/LocalState"


class Action(BaseModel):
    """The common action subsection.

    This should fit the schema for actions as defined in the documentation.
    :attr keys: the keys to press to call the action.
    :attr command: The string or dictionary for the command. The program assumes that you
        didn't fuck it up and will not bother validating it.
    """

    keys: str
    command: Union[str, Dict]


class Scheme(BaseModel):
    """The common colorscheme subsection.

    The field should be self evident.
    """

    background: str
    black: str
    blue: str
    brightBlack: str
    brightBlue: str
    brightCyan: str
    brightGreen: str
    brightPurple: str
    brightRed: str
    brightWhite: str
    brightYellow: str
    cursorColor: str
    cyan: str
    foreground: str
    green: str
    name: str
    purple: str
    red: str
    selectionBackground: str
    white: str
    yellow: str


class Profile(BaseModel):
    """A model for a profile object."""

    class Font:
        face: str
        size: int

    # Styling
    bellStyle: Optional[str]
    font: Optional[Font]
    useAcrylic: bool = False

    # One of these
    commandline: Optional[str]
    source: Optional[str]

    # Metadata
    guid: str
    hidden: bool
    name: str


class Profiles(BaseModel):
    """The profiles section."""

    defaults: Profile
    list: List[Profile]


class WTSettingsCommonSchema(BaseModel):
    """Commmon fields between the json and yaml documents."""

    copyFormatting: str
    copyOnSelect: bool
    defaultProfile: str
    profiles: Profiles
    schemes: List[Schemes]


class WTSettingsJSONSchema(WTSettingsCommonSchema):
    """A Json for the windows terminal schemas."""

    def load(cls, config: Optional[Config] = None) -> "WTSettingsJSONSchema":

        filepath = config.JSONConfig
        with open(filepath, "r") as file:
            return cls(**yaml.safe_load(file))

    actions: List[Action]


class WTSettingsYAMLSchema(WTSettingsCommonSchema):
    """How the YAML document should look."""

    # Configuration dependent methods
    @classmethod
    def load(
        cls, config: Optional[Config] = None, confattr: Optional[str] = None
    ) -> "WTSettingsYAMLSchema":

        config = config or Config()

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

    actions: Dict[str, List[Action]]
