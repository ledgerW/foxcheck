{pkgs}: {
  deps = [
    pkgs.bash
    pkgs.libxcrypt
    pkgs.rustc
    pkgs.libiconv
    pkgs.cargo
    pkgs.postgresql
  ];
}
