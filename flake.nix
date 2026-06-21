{
  description = "Marp slide template dev environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.nodejs_22
            # marp の PDF / PPTX / 画像エクスポートに使うブラウザ
            pkgs.chromium
          ];

          # marp-cli (puppeteer) が参照する Chrome の実行パス
          CHROME_PATH = "${pkgs.chromium}/bin/chromium";

          shellHook = ''
            echo "node $(node --version) / npm $(npm --version)"
          '';
        };
      });
}
