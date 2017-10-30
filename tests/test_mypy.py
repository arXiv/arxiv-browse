import os
import glob
import subprocess
import unittest


class MyPyTest(unittest.TestCase):

    def test_run_mypy_module(self):
        browse_result: int = subprocess.call(["mypy", "-p", self.pkgname], env=os.environ, cwd=self.pypath)
        self.assertEqual(browse_result, 0, 'mypy on browse')

    def test_run_mypy_tests(self):
        for test_file in glob.iglob(f'{os.getcwd()}/tests/**/*.py', recursive=True):
            test_result: int = subprocess.call(["mypy", test_file], env=os.environ, cwd=self.pypath)
            self.assertEqual(test_result, 0, f'mypy on test {test_file}')

    def __init__(self, *args, **kwargs) -> None:
            self.pkgname: str = "browse"
            super(MyPyTest, self).__init__(*args, **kwargs)
            my_env = os.environ.copy()
            self.pypath: str = my_env.get("PYTHONPATH", os.getcwd())


if __name__ == '__main__':
    unittest.main()
