"""Tests using mypy."""
import os
import glob
import subprocess
import unittest
from typing import List


class MyPyTest(unittest.TestCase):
    """Class for testing modules with mypy."""

    def test_run_mypy_module(self) -> None:
        """Run mypy on all module sources."""
        mypy_call: List[str] = ["mypy"] + self.mypy_opts + ["-p", self.pkgname]
        browse_result: int = subprocess.call(
            mypy_call, env=os.environ, cwd=self.pypath)
        self.assertEqual(browse_result, 0, 'mypy on browse')

    # TODO: do we need this?
    # def test_run_mypy_tests(self) -> None:
    #     """Run mypy on all tests in module under the tests directory."""
    #     for test_file in glob.iglob(f'{os.getcwd()}/tests/**/*.py',
    #                                 recursive=True):
    #         mypy_call: List[str] = ["mypy"] + self.mypy_opts + [test_file]
    #         test_result: int = subprocess.call(
    #             mypy_call, env=os.environ, cwd=self.pypath)
    #         self.assertEqual(test_result, 0, f'mypy on test {test_file}')

    def __init__(self, *args, **kwargs):  # type: ignore
        """Set up some common variables."""
        self.pkgname: str = "browse"
        super(MyPyTest, self).__init__(*args, **kwargs)
        my_env = os.environ.copy()
        self.pypath: str = my_env.get("PYTHONPATH", os.getcwd())
        self.mypy_opts: List[str] = ['--ignore-missing-imports']


if __name__ == '__main__':
    unittest.main()
