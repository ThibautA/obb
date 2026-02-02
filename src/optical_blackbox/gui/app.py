"""Simple GUI for encrypting and decrypting optical design files.

This module provides a lightweight tkinter-based interface for testing
the OpticalBlackBox encryption functionality without command-line usage.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from datetime import datetime
import json

from optical_blackbox.crypto.keys import KeyManager
from optical_blackbox.crypto.hybrid import OBBEncryptor, OBBSigner
from optical_blackbox.serialization.pem import public_key_to_pem, public_key_from_pem
from optical_blackbox.serialization.binary import BinaryWriter, BinaryReader
from optical_blackbox.serialization import json_codec
from optical_blackbox.parsers.registry import parse_file
from optical_blackbox.formats.obb_constants import OBB_MAGIC
from optical_blackbox.models.metadata import OBBMetadata
from optical_blackbox.exceptions import InvalidMagicBytesError


class CryptoGUI:
    """Simple GUI for file encryption/decryption."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the GUI.

        Args:
            root: The root tkinter window.
        """
        self.root = root
        self.root.title("Optical BlackBox - Crypto Tool")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create the user interface."""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Section 1: Keys
        keys_frame = ttk.LabelFrame(main_frame, text="Keys", padding="10")
        keys_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(keys_frame, text="Public Key (.pem):").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.public_key_var = tk.StringVar()
        ttk.Entry(keys_frame, textvariable=self.public_key_var, width=40).grid(
            row=0, column=1, padx=5
        )
        ttk.Button(keys_frame, text="Browse...", command=self._browse_public_key).grid(
            row=0, column=2, padx=2
        )
        ttk.Button(keys_frame, text="Generate Keys", command=self._generate_keypair).grid(
            row=0, column=3, padx=2
        )

        ttk.Label(keys_frame, text="Private Key (.pem):").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.private_key_var = tk.StringVar()
        ttk.Entry(keys_frame, textvariable=self.private_key_var, width=40).grid(
            row=1, column=1, padx=5
        )
        ttk.Button(keys_frame, text="Browse...", command=self._browse_private_key).grid(
            row=1, column=2, padx=2
        )

        # Section 2: File
        file_frame = ttk.LabelFrame(main_frame, text="File", padding="10")
        file_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(file_frame, text="Input File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.input_file_var, width=50).grid(
            row=0, column=1, padx=5
        )
        ttk.Button(file_frame, text="Browse...", command=self._browse_input_file).grid(
            row=0, column=2
        )

        ttk.Label(
            file_frame, text="(.zmx for encrypt, .obb for decrypt)", font=("", 8)
        ).grid(row=1, column=1, sticky=tk.W)

        # Section 3: Actions
        actions_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
        actions_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)

        button_frame = ttk.Frame(actions_frame)
        button_frame.grid(row=0, column=0, pady=5)

        ttk.Button(
            button_frame, text="Encrypt to .obb", command=self._encrypt, width=20
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            button_frame, text="Decrypt .obb", command=self._decrypt, width=20
        ).pack(side=tk.LEFT, padx=5)

        # Status
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)

        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            status_frame, textvariable=self.status_var, foreground="blue"
        )
        self.status_label.pack(side=tk.LEFT, padx=5)

    def _browse_public_key(self) -> None:
        """Open file dialog for public key."""
        filename = filedialog.askopenfilename(
            title="Select Public Key",
            filetypes=[("PEM files", "*.pem"), ("All files", "*.*")],
        )
        if filename:
            self.public_key_var.set(filename)

    def _browse_private_key(self) -> None:
        """Open file dialog for private key."""
        filename = filedialog.askopenfilename(
            title="Select Private Key",
            filetypes=[("PEM files", "*.pem"), ("All files", "*.*")],
        )
        if filename:
            self.private_key_var.set(filename)

    def _browse_input_file(self) -> None:
        """Open file dialog for input file."""
        filename = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[
                ("Zemax files", "*.zmx"),
                ("OBB files", "*.obb"),
                ("All files", "*.*"),
            ],
        )
        if filename:
            self.input_file_var.set(filename)

    def _generate_keypair(self) -> None:
        """Generate a new keypair and save to files."""
        try:
            # Ask user where to save the keys
            directory = filedialog.askdirectory(
                title="Select Directory to Save Keys",
                initialdir=Path.home(),
            )
            
            if not directory:
                return

            directory_path = Path(directory)
            
            # Ask for a prefix/name for the keys
            from tkinter import simpledialog
            prefix = simpledialog.askstring(
                "Key Name",
                "Enter a name for the keys (e.g., 'mykey'):",
                initialvalue="gui_key"
            )
            
            if not prefix:
                return

            self._update_status("Generating keypair...")

            # Generate keypair
            key_manager = KeyManager()
            private_key, public_key = key_manager.generate_keypair()

            # Save keys
            private_key_path = directory_path / f"{prefix}_private.pem"
            public_key_path = directory_path / f"{prefix}_public.pem"

            key_manager.save_private_key(private_key, private_key_path)
            key_manager.save_public_key(public_key, public_key_path)

            # Update UI fields
            self.public_key_var.set(str(public_key_path))
            self.private_key_var.set(str(private_key_path))

            self._update_status("Keys generated successfully!")
            messagebox.showinfo(
                "Success",
                f"Keys generated successfully!\n\n"
                f"Public key: {public_key_path.name}\n"
                f"Private key: {private_key_path.name}\n\n"
                f"Saved in: {directory_path}"
            )

        except Exception as e:
            self._update_status(f"Error: {str(e)}", is_error=True)
            messagebox.showerror("Key Generation Failed", str(e))

    def _update_status(self, message: str, is_error: bool = False) -> None:
        """Update status label.

        Args:
            message: Status message to display.
            is_error: Whether this is an error message.
        """
        self.status_var.set(message)
        self.status_label.config(foreground="red" if is_error else "green")
        self.root.update()

    def _encrypt(self) -> None:
        """Encrypt a Zemax file to .obb format."""
        try:
            # Validate inputs
            input_path = Path(self.input_file_var.get())
            if not input_path.exists():
                raise ValueError("Input file does not exist")

            public_key_path = Path(self.public_key_var.get())
            if not public_key_path.exists():
                raise ValueError("Public key file does not exist")

            private_key_path = Path(self.private_key_var.get())
            if not private_key_path.exists():
                raise ValueError("Private key file does not exist")

            self._update_status("Parsing input file...")

            # Parse input file
            result = parse_file(input_path)
            if result.is_err():
                raise ValueError(f"Failed to parse file: {result.unwrap_err()}")

            surface_group = result.unwrap()

            self._update_status("Encrypting...")

            # Load keys
            key_manager = KeyManager()
            public_key = key_manager.load_public_key(public_key_path)
            private_key = key_manager.load_private_key(private_key_path)

            # Serialize surface group to JSON
            surfaces_data = {
                "surfaces": [surface.model_dump() for surface in surface_group.surfaces],
                "wavelengths": surface_group.wavelengths,
                "fields": surface_group.fields,
            }
            plaintext = json_codec.dumps(surfaces_data).encode("utf-8")

            # Encrypt
            encrypted_payload, ephemeral_public_key = OBBEncryptor.encrypt(
                plaintext, public_key
            )

            # Sign
            signature = OBBSigner.sign(encrypted_payload, private_key)

            # Create metadata
            metadata = OBBMetadata(
                format_version="1.0",
                vendor_id="GUI",
                vendor_name="GUI User",
                description=f"Encrypted from {input_path.name}",
                part_number=input_path.stem,
                efl_mm=surface_group.effective_focal_length,
                na=surface_group.numerical_aperture,
                clear_aperture_mm=surface_group.clear_aperture_diameter,
                spectral_range_nm=surface_group.spectral_range,
                num_surfaces=surface_group.num_surfaces,
                signature=signature,
                created_at=datetime.utcnow(),
            )

            # Build header
            header = metadata.model_dump(mode="json")
            header["ephemeral_public_key"] = public_key_to_pem(ephemeral_public_key)
            header_bytes = json_codec.dumps(header, indent=2).encode("utf-8")

            # Write .obb file
            output_path = input_path.with_suffix(".obb")
            with open(output_path, "wb") as f:
                writer = BinaryWriter(f)
                writer.write_magic(OBB_MAGIC)
                writer.write_length_prefixed(header_bytes)
                writer.write_bytes(encrypted_payload)

            self._update_status(f"Success! Saved to {output_path.name}")
            messagebox.showinfo(
                "Success", f"File encrypted successfully!\n\nOutput: {output_path}"
            )

        except Exception as e:
            self._update_status(f"Error: {str(e)}", is_error=True)
            messagebox.showerror("Encryption Failed", str(e))

    def _decrypt(self) -> None:
        """Decrypt a .obb file."""
        try:
            # Validate inputs
            input_path = Path(self.input_file_var.get())
            if not input_path.exists():
                raise ValueError("Input file does not exist")

            if input_path.suffix != ".obb":
                raise ValueError("Input file must be a .obb file")

            public_key_path = Path(self.public_key_var.get())
            if not public_key_path.exists():
                raise ValueError("Public key file does not exist")

            private_key_path = Path(self.private_key_var.get())
            if not private_key_path.exists():
                raise ValueError("Private key file does not exist")

            self._update_status("Reading .obb file...")

            # Load keys
            key_manager = KeyManager()
            public_key = key_manager.load_public_key(public_key_path)
            private_key = key_manager.load_private_key(private_key_path)

            # Read .obb file
            with open(input_path, "rb") as f:
                reader = BinaryReader(f)

                # Verify magic bytes
                if not reader.read_and_verify_magic(OBB_MAGIC):
                    raise InvalidMagicBytesError()

                # Read header
                header_bytes = reader.read_length_prefixed()
                header = json_codec.loads(header_bytes.decode("utf-8"))

                # Extract metadata and ephemeral key
                metadata = OBBMetadata(**{
                    k: v for k, v in header.items() if k != "ephemeral_public_key"
                })
                ephemeral_public_key = public_key_from_pem(header["ephemeral_public_key"])

                # Read encrypted payload
                encrypted_payload = reader.read_remaining()

            self._update_status("Verifying signature...")

            # Verify signature
            if not OBBSigner.verify(encrypted_payload, metadata.signature, public_key):
                raise ValueError("Signature verification failed!")

            self._update_status("Decrypting...")

            # Decrypt
            plaintext = OBBEncryptor.decrypt(
                encrypted_payload, ephemeral_public_key, private_key
            )

            # Parse surface data
            surface_data = json_codec.loads(plaintext.decode("utf-8"))

            # Save decrypted JSON
            output_path = input_path.with_suffix(".decrypted.json")
            with open(output_path, "w") as f:
                json.dump(
                    {
                        "metadata": metadata.model_dump(),
                        "data": surface_data,
                    },
                    f,
                    indent=2,
                )

            self._update_status(f"Success! Saved to {output_path.name}")
            messagebox.showinfo(
                "Success",
                f"File decrypted successfully!\n\n"
                f"Vendor: {metadata.vendor_name}\n"
                f"Part: {metadata.part_number}\n"
                f"Surfaces: {metadata.num_surfaces}\n\n"
                f"Output: {output_path}",
            )

        except Exception as e:
            self._update_status(f"Error: {str(e)}", is_error=True)
            messagebox.showerror("Decryption Failed", str(e))


def run_gui() -> None:
    """Launch the GUI application."""
    try:
        root = tk.Tk()
        app = CryptoGUI(root)
        root.mainloop()
    except ImportError as e:
        print(f"Error: tkinter is not available. {e}")
        print("On Linux, install: sudo apt-get install python3-tk")
        raise
