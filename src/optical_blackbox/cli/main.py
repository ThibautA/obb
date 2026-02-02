"""Optical BlackBox CLI.

Command-line interface for creating and managing encrypted optical designs.
"""

import click

from optical_blackbox.cli.commands import keygen_command, create_command, inspect_command


@click.group()
@click.version_option(package_name="optical-blackbox")
def main() -> None:
    """Optical BlackBox - Encrypted optical design distribution.

    Create and manage encrypted .obb files for secure distribution
    of optical designs.

    \b
    Commands:
      keygen   Generate ECDSA P-256 key pair
      create   Create encrypted .obb from Zemax file
      inspect  View .obb metadata (no decryption)
      gui      Launch graphical interface (optional)

    \b
    Examples:
      obb keygen ./keys --prefix vendor
      obb create lens.zmx lens.obb -k private.pem -v my-company -n "50mm Lens"
      obb inspect lens.obb
      obb gui
    """
    pass


@click.command()
def gui_command() -> None:
    """Launch the graphical interface for encryption/decryption.

    Opens a simple GUI for testing encryption and decryption
    functionality without using command-line arguments.
    """
    try:
        # Lazy import to avoid tkinter dependency for CLI-only users
        from optical_blackbox.gui.app import run_gui
        run_gui()
    except ImportError as e:
        click.echo(f"Error: Could not launch GUI. {e}", err=True)
        click.echo("On Linux, you may need to install: sudo apt-get install python3-tk")
        raise click.Abort()


# Register commands
main.add_command(keygen_command, name="keygen")
main.add_command(create_command, name="create")
main.add_command(inspect_command, name="inspect")
main.add_command(gui_command, name="gui")


if __name__ == "__main__":
    main()
