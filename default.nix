with import <nixpkgs> {};
with pkgs.python36Packages;

stdenv.mkDerivation {
  name = "impurePythonEnv";
  buildInputs = [
    # these packages are required for virtualenv and pip to work:
    #
    python36Full
    python36Packages.virtualenv
    python36Packages.pip
    # the following packages are related to the dependencies of your python
    # project.
    # In this particular example the python modules listed in the
    # requirements.tx require the following packages to be installed locally
    # in order to compile any binary extensions they may require.
    #
    gcc6
    mysql57
    openssl
    zlib
  ];
  src = null;
  shellHook = ''
    # set SOURCE_DATE_EPOCH so that we can use python wheels
    SOURCE_DATE_EPOCH=$(date +%s)
    virtualenv venv
    export PATH=$PWD/venv/bin:$PATH
    export PYTHONPATH=$PWD
    pip install -r requirements.txt
    export LD_LIBRARY_PATH=${mysql57}/lib:${gcc6.cc.lib}/lib:$LD_LIBRARY_PATH
    export FLASK_APP=app.py
    export FLASK_DEBUG=1
    source private_vars.sh
  '';
}
