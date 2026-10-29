"""Overview of the pyddt command-line tools."""

import argparse


def cmdline_define():
    """Build the parser for the toolkit overview."""
    return argparse.ArgumentParser(
        prog="pyddt",
        description="Python tools for preparing and analyzing DVM-DOS-TEM runs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Available commands:
  pyddt-input     Validate, crop, and plot input NetCDF files.
  pyddt-outspec   List and enable variables in output specification files.
  pyddt-param     Read, edit, and convert model parameter files.
  pyddt-runmask   Create, modify, and view grid-cell run masks.
  pyddt-swd       Set up a model working directory.
  pyddt-qcal      Compare model results with calibration targets.

Run <command> --help for options, for example: pyddt-input --help.
These tools are separate commands; invoke them by their full names.""",
    )


def cmdline_parse(argv=None):
    """Parse command-line arguments."""
    return cmdline_define().parse_args(argv)


def cmdline_run(args):
    """Display the toolkit overview."""
    cmdline_define().print_help()


def cmdline_entry():
    """Run the command using arguments from the shell."""
    return main()


def main(argv=None):
    """Display usage when invoked without arguments or with --help."""
    return cmdline_run(cmdline_parse(argv))
