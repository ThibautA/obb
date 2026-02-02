"""OBB file creation command.

Creates encrypted .obb files from Zemax designs.
"""

from pathlib import Path

import click

from optical_blackbox.crypto.keys import KeyManager
from optical_blackbox.parsers import ZemaxParser
from optical_blackbox.optics import extract_metadata
from optical_blackbox.formats import OBBWriter
from optical_blackbox.cli.output.console import console, print_success, print_error, print_info
from optical_blackbox.cli.output.formatters import format_creation_result


@click.command("create")
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("output_file", type=click.Path(dir_okay=False, path_type=Path))
@click.option(
    "--private-key",
    "-k",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to vendor private key (PEM)",
)
@click.option(
    "--vendor-id",
    "-v",
    required=True,
    help="Vendor identifier (3-50 chars, lowercase alphanumeric)",
)
@click.option(
    "--name",
    "-n",
    required=True,
    help="Component name",
)
@click.option(
    "--description",
    "-d",
    default=None,
    help="Component description",
)
@click.option(
    "--part-number",
    "-p",
    default=None,
    help="Part number",
)
@click.option(
    "--recipient-key",
    "-r",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Recipient public key for encryption (optional)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing output file",
)
def create_command(
    input_file: Path,
    output_file: Path,
    private_key: Path,
    vendor_id: str,
    name: str,
    description: str | None,
    part_number: str | None,
    recipient_key: Path | None,
    force: bool,
) -> None:
    """Create an encrypted OBB file from a Zemax design.

    INPUT_FILE: Zemax file (.zmx or .zar)
    OUTPUT_FILE: Output .obb file path
    """
    # Check output
    if output_file.exists() and not force:
        print_error(f"Output file exists: {output_file}")
        print_error("Use --force to overwrite")
        raise SystemExit(1)

    # Ensure .obb extension
    if output_file.suffix.lower() != ".obb":
        output_file = output_file.with_suffix(".obb")

    # Load vendor key
    print_info("Loading vendor key...")
    vendor_key_manager = KeyManager()
    vendor_key_manager.load_private_key(private_key)

    # Load recipient key if provided
    recipient_key_manager: KeyManager | None = None
    if recipient_key:
        print_info("Loading recipient key...")
        recipient_key_manager = KeyManager()
        recipient_key_manager.load_public_key(recipient_key)

    # Parse input file
    print_info(f"Parsing {input_file.name}...")
    parser = ZemaxParser()
    result = parser.parse(input_file)

    if not result.is_ok():
        print_error(f"Failed to parse: {result.error}")
        raise SystemExit(1)

    surface_group = result.unwrap()
    console.print(f"  [dim]Found {surface_group.num_surfaces} surfaces[/dim]")

    # Extract metadata
    print_info("Computing optical properties...")
    metadata = extract_metadata(
        surface_group=surface_group,
        vendor_id=vendor_id,
        name=name,
        description=description,
        part_number=part_number,
    )

    console.print(f"  [dim]EFL: {metadata.efl_mm:.2f} mm, NA: {metadata.na:.4f}[/dim]")

    # Create OBB file
    print_info("Creating encrypted OBB file...")
    writer = OBBWriter(vendor_key_manager)

    writer.write(
        surfaces=surface_group,
        metadata=metadata,
        output_path=output_file,
        recipient_public_key=recipient_key_manager.get_public_key() if recipient_key_manager else None,
    )

    # Get file size
    file_size = output_file.stat().st_size

    # Display result
    console.print()
    console.print(format_creation_result(str(output_file), metadata, file_size))
    console.print()
    print_success(f"Created {output_file}")
