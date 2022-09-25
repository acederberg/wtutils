# About

This project is really just for fun. I don't like the way that windows terminal customization works and would like to do this a better way.


# Installation

Install using the following steps:

~~~bash
git clone https://github.com/acederberg/wtutil
cd wtutil

# The prefix flag is not nescessary.
python3.10 -m pip install -e . --prefix $( realpath ~/.local/lib/python3.10/site-packages/ )

# This step is bash specific and is specific to path specified by the prefix flag above.
# Otherwise add your python3.10 binaries to your path.
echo 'export PATH="$PATH:$( realpath ~/.local/bin )"
~~~


# Usage

For now just use `wtsettings` to get the interactive prompt.


