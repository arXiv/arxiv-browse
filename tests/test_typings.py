"""Tests using mypy."""
import glob
import os
import subprocess
import unittest
from subprocess import CalledProcessError
from typing import Dict, List
from unittest import TestCase


class MyPyTest(TestCase):
    """Class for testing modules with mypy."""

    def test_run_mypy_module(self) -> None:
        """Run mypy on all module sources."""
        pypath: str = os.environ.get("PYTHONPATH", os.getcwd())
        result: int = subprocess.call(["mypy"] + ["-p", "browse"],
                                      env=os.environ, cwd=pypath)
        self.assertEqual(result, 0, 'Expect 0 type errors when running mypy on browse')

    # def __init__(self, *args: str, **kwargs: Dict) -> None:
    #     """Set up some common variables."""
    #     super().__init__(*args, **kwargs)
    #     self.pkgname: str = "browse"
    #     my_env = os.environ.copy()



if __name__ == '__main__':
    unittest.main()
