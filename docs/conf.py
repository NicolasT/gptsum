"""Sphinx configuration."""
from datetime import datetime

import gptsum


project = "gptsum"
author = "Nicolas Trangez"
copyright = f"{datetime.now().year}, {author}"

version = gptsum.__version__
release = version

html_theme = "furo"
