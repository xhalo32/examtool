{
  description = "EXAM Tool";

  outputs =
    { self }:
    let
      system = "x86_64-linux";
    in
    with (import ./. { inherit system; });
    {
      packages.${system}.default = default;
      devShells.${system}.default = shell;
    };
}
