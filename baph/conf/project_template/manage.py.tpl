#!/usr/bin/env python
import os
import sys


if __name__ == "__main__":
  os.environ.setdefault("FLASK_SETTINGS_MODULE", "{{ project_name }}.settings")
  try:
    from baph.core.cli import execute_from_command_line
  except ImportError:
    raise ImportError(
      "Couldn't import Baph. Are you sure it's installed and available "
      "on your PATH environment variable? Did you forget to activate a "
      "virtual environment?"
    )
  execute_from_command_line(sys.argv)
