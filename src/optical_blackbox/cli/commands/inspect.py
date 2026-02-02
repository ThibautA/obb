"""OBB file inspection command.

Displays metadata from .obb files without decryption.
"""

from pathlib import Path

import click

from optical_blackbox.formats import OBBReader
from optical_blackbox.cli.output.console import console, print_error
from optical_blackbox.cli.output.formatters import print_metadata


@click.command("inspect")
@click.argument("obb_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output as JSON",
)
def inspect_command(obb_file: Path, as_json: bool) -> None:
    """Inspect metadata from an OBB file.

    OBB_FILE: Path to .obb file
    """
    reader = OBBReader()

    result = reader.read_metadata(obb_file)

    if not result.is_ok():
        print_error(f"Failed to read: {result.error}")
        raise SystemExit(1)

    metadata = result.unwrap()

    if as_json:
        # JSON output
        import json
        from optical_blackbox.serialization.json_codec import OBBJSONEncoder

        console.print(json.dumps(metadata.model_dump(), cls=OBBJSONEncoder, indent=2))
    else:
        # Rich table output
        print_metadata(metadata)
