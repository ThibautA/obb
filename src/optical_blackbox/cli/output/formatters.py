"""Output formatters for CLI display.

Provides Rich tables and panels for structured data display.
"""

from typing import Any

from rich.panel import Panel
from rich.table import Table

from optical_blackbox.models.metadata import OBBMetadata
from optical_blackbox.cli.output.console import console


def format_metadata_table(metadata: OBBMetadata) -> Table:
    """Format metadata as a Rich table.

    Args:
        metadata: OBB metadata

    Returns:
        Rich Table ready for display
    """
    table = Table(title="OBB Metadata", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="dim")
    table.add_column("Value", style="magenta")

    table.add_row("Version", metadata.version)
    table.add_row("Vendor ID", metadata.vendor_id)
    table.add_row("Name", metadata.name)

    if metadata.description:
        table.add_row("Description", metadata.description)

    if metadata.part_number:
        table.add_row("Part Number", metadata.part_number)

    # Optical properties
    efl_str = f"{metadata.efl_mm:.2f} mm" if metadata.efl_mm != float("inf") else "∞ (afocal)"
    table.add_row("EFL", efl_str)
    table.add_row("NA", f"{metadata.na:.4f}")
    table.add_row("Diameter", f"{metadata.diameter_mm:.2f} mm")

    # Spectral range
    if metadata.spectral_range_nm:
        table.add_row(
            "Spectral Range",
            f"{metadata.spectral_range_nm[0]:.1f} - {metadata.spectral_range_nm[1]:.1f} nm",
        )

    table.add_row("Surfaces", str(metadata.num_surfaces))

    if metadata.created_at:
        table.add_row("Created", metadata.created_at.isoformat())

    # Signature status
    if metadata.signature:
        table.add_row("Signature", "[green]Present[/green]")
    else:
        table.add_row("Signature", "[yellow]None[/yellow]")

    return table


def format_key_info(key_type: str, key_path: str, fingerprint: str) -> Panel:
    """Format key information as a panel.

    Args:
        key_type: "public" or "private"
        key_path: Path where key was saved
        fingerprint: Key fingerprint (first 8 chars of hash)

    Returns:
        Rich Panel for display
    """
    content = f"""[bold]Key Type:[/bold] {key_type.upper()}
[bold]Fingerprint:[/bold] {fingerprint}
[bold]Saved to:[/bold] [path]{key_path}[/path]"""

    title = f"🔑 {key_type.capitalize()} Key Generated"
    return Panel(content, title=title, border_style="green")


def format_creation_result(
    output_path: str,
    metadata: OBBMetadata,
    file_size: int,
) -> Panel:
    """Format OBB creation result as a panel.

    Args:
        output_path: Path to created .obb file
        metadata: Created file metadata
        file_size: File size in bytes

    Returns:
        Rich Panel for display
    """
    size_kb = file_size / 1024

    content = f"""[bold]Output:[/bold] [path]{output_path}[/path]
[bold]Size:[/bold] {size_kb:.1f} KB
[bold]Surfaces:[/bold] {metadata.num_surfaces}
[bold]EFL:[/bold] {metadata.efl_mm:.2f} mm
[bold]NA:[/bold] {metadata.na:.4f}"""

    return Panel(content, title="✓ OBB File Created", border_style="green")


def print_metadata(metadata: OBBMetadata) -> None:
    """Print metadata to console.

    Args:
        metadata: OBB metadata to display
    """
    table = format_metadata_table(metadata)
    console.print(table)


def print_dict(data: dict[str, Any], title: str = "Data") -> None:
    """Print a dictionary as a table.

    Args:
        data: Dictionary to display
        title: Table title
    """
    table = Table(title=title, show_header=True)
    table.add_column("Key", style="dim")
    table.add_column("Value", style="magenta")

    for key, value in data.items():
        table.add_row(str(key), str(value))

    console.print(table)
