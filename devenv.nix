{ pkgs, ... }:

{
  env = {
    BIN_PATH = "bin";
  };

  enterShell = ''
    # See to it that cloud-sql-proxy is installed in to dev env
    make $BIN_PATH/cloud-sql-proxy
  '';

  packages = [
    pkgs.git
    pkgs.libmysqlclient
  ];

  languages.python = {
    enable = true;
    poetry = {
      enable = true;
      activate.enable = true;
      install.enable = true;
    };
    venv.enable = true;
  };
}
