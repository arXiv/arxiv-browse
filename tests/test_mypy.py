import os
import subprocess
import unittest


class MyPyTest(unittest.TestCase):

    def test_run_mypy(self):
        my_env = os.environ.copy()
        pypath: str = my_env.get("PYTHONPATH", '')
        browse_result: int = subprocess.call(["mypy", "-p", self.pkgname], env=os.environ, cwd=pypath)
        self.assertEqual(browse_result, 0, 'mypy on browse')

    def __init__(self, *args, **kwargs) -> None:
        self.pkgname: str = "browse"
        super(MyPyTest, self).__init__(*args, **kwargs)


if __name__ == '__main__':
    unittest.main()
