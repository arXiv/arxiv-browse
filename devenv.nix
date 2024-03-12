{ pkgs, ... }:

{
  packages = [
    pkgs.git
    pkgs.libmysqlclient
  ];

  languages.python = {
    enable = true;
    poetry = {
      enable = true;
      activate.enable = true;
    };
    venv.enable = true;
  };
}
