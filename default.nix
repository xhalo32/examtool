{
  sources ? import ./npins,
  system ? builtins.currentSystem,
  pkgs ? import sources.nixpkgs {
    inherit system;
    config = { };
    overlays = [ ];
  },
}@inputs:
rec {
  python3Packages.examtool = pkgs.python3.pkgs.buildPythonApplication {
    name = "examtool";
    version = "0.1.0";
    src = ./.;
    pyproject = true;
    checkPhase = ''
      pytest -q typst_exam/test.py
    '';
    nativeBuildInputs = with pkgs.python3Packages; [
      pytest
    ];
    propagatedBuildInputs = with pkgs.python3Packages; [
      requests
      markdown
      setuptools
    ];
  };
  default = python3Packages.examtool;
  shell = pkgs.mkShellNoCC {
    packages = with pkgs; [
      default
      npins
      typst
      jq
      (python3.withPackages (
        ps: with ps; [
          requests
          markdown
          setuptools
          pytest
        ]
      ))
    ];
  };
}
