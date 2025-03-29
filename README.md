# EXAM Tool -- EaC Integration Platform

A simple Python tool for programmatically working with Aalto University's EXAM system.
In particular, this tool follows the _Exam as Code_ (EaC for short) philosophy, and makes it easy to create university exams using a supported _Rich Text Format_ (or RTF).

A compatibility layer called _EaC Intermediate Representation_ (or EaC IR), based on the _JavaScript Object Notation_ (or JSON) technology, stands between the RTF and EXAM Tool to unify, standardize and accelerate the creation and adoption of EaC-based tooling and infrastructure.

Currently supported RTF formats are

| Supported format | Notes |
|---|---|
| [typst](https://typst.app) | A minimal subset of the typst language is supported. |

## Components

- `examtool.py`: Primary tool for interacting with EXAM.
- `sdk.py`: A library for making various REST API calls to EXAM.
  Covers only a tiny subset of EXAM's endpoints -- those which are needed to create an exam from the EaC IR.
- `typst_exam.py`: Sample tool to convert [typst](https://typst.app) to EaC IR. See [examples here](#typst-exam)

## Getting started

1. ~~Clone this repository.~~ [Install Nix](https://docs.determinate.systems/getting-started/individuals/).
   [Nix](https://nixos.org/) is a purely functional package manager, with Nix, you don't need Pip or even Python to use this tool.
   > Make sure flake support is enabled in your Nix installation!
2. ~~Install the requirements using `pip install requests markdown`.~~ Run `nix shell github:xhalo32/examtool`.
3. Set the `EXAM_COOKIE` environment variable with fresh cookies from a browser login to <https://exam.aalto.fi>
   ```
   EXAM_COOKIE=XSRF-TOKEN=abcd;_shibsession_abcd=abcd;PLAY_SESSION=abcd
   ```
   > Required cookies are `XSRF-TOKEN`, `_shibsession_...` and `PLAY_SESSION`. The browser session should work concurrently while using the tool.
4. See the tool's help `examtool -h`.
5. For example, to list your exams, run
   ```sh
   examtool get exams
   ```
   You should look for your `owner_id` and record it somewere.
6. Import an exam. First, get your exam id from EXAM (it's in the URL). Then, run the following command to import the example
   ```sh
   examtool import EXAM_ID OWNER_ID example.json
   ```
   The tool will create all the declared questions and tags them so that it knows how to delete them when you import again -- which you should try and make sure works as you expect.

## Commands

See the help (`-h`) page for each subcommand for more information.

## Typst EXAM

Run

```sh
typst_exam EXAMple.typ |jq
```

to see the EaC IR generated from the typst file.

## Bugs and known issues

Report bugs directly here on GitHub.

Currently known issues:
- Creating a question will URI encode special characters. A temporary workaround (i.e. HACK) is in place to fix this.

## Copyright and license

Copyright (C) 2025 Niklas Halonen

This project is licensed under GPL version 3.0. See the [COPYING](./COPYING) file for details.