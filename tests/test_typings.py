"""Tests using mypy."""
import os
import glob
import subprocess
import unittest
from typing import Dict, List
from unittest import TestCase

class MyPyTest(TestCase):
    """Class for testing modules with mypy."""

    def test_run_mypy_module(self) -> None:
        """Run mypy on all module sources."""
        mypy_call: List[str] = ["mypy"] + self.mypy_opts + ["-p", self.pkgname]
        result: int = subprocess.call(
            mypy_call, env=os.environ, cwd=self.pypath)
        self.assertEqual(result, 0, f'mypy on {self.pkgname}')

    def test_run_mypy_tests(self) -> None:
        """Run mypy on all tests in module under the tests directory."""
        for test_file in glob.iglob(f'{os.getcwd()}/tests/**/*.py',
                                    recursive=True):
            mypy_call: List[str] = ["mypy"] + self.mypy_opts + [test_file]
            test_result: int = subprocess.call(
                mypy_call, env=os.environ, cwd=self.pypath)
            print(test_result)    # Kind of nice to see what failed.
            self.assertEqual(test_result, 0, f'mypy on test {test_file}')

    def __init__(self, *args: str, **kwargs: Dict) -> None:
        """Set up some common variables."""
        super().__init__(*args, **kwargs)
        self.pkgname: str = "browse"
        my_env = os.environ.copy()
        self.pypath: str = my_env.get("PYTHONPATH", os.getcwd())
        self.mypy_opts: List[str] = [] # should now use mypy.ini for mypy options
        # self.mypy_opts: List[str] = ['--ignore-missing-imports', '--strict']


if __name__ == '__main__':
    unittest.main()
