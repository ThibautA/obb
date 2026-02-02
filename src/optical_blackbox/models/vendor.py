"""Vendor information model.

Defines vendor data for the PKI registry.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class VendorInfo(BaseModel):
    """Vendor information for the PKI registry.

    Stores vendor details and their public key for signature verification.

    Attributes:
        vendor_id: Unique vendor identifier
        company_name: Company display name
        public_key_pem: PEM-encoded ECDSA public key
        contact_email: Contact email address
        website: Optional website URL
        registered_at: Registration timestamp
        key_version: Key version for rotation tracking
        is_active: Whether vendor is currently active
    """

    vendor_id: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-z0-9][a-z0-9\-]*$",
        description="Unique vendor identifier",
    )
    company_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Company display name",
    )
    public_key_pem: str = Field(
        ...,
        description="PEM-encoded ECDSA public key",
    )
    contact_email: str = Field(
        ...,
        description="Contact email address",
    )
    website: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Company website URL",
    )
    registered_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Registration timestamp (UTC)",
    )
    key_version: int = Field(
        default=1,
        ge=1,
        description="Key version for rotation tracking",
    )
    is_active: bool = Field(
        default=True,
        description="Whether vendor is currently active",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "vendor_id": "thorlabs",
                "company_name": "Thorlabs Inc.",
                "public_key_pem": "-----BEGIN PUBLIC KEY-----\n...",
                "contact_email": "support@thorlabs.com",
                "website": "https://www.thorlabs.com",
                "registered_at": "2026-01-30T10:00:00Z",
                "key_version": 1,
                "is_active": True,
            }
        }
    }


class VendorRegistration(BaseModel):
    """Request model for vendor registration.

    Attributes:
        vendor_id: Unique vendor identifier
        company_name: Company display name
        public_key_pem: PEM-encoded ECDSA public key
        contact_email: Contact email address
        website: Optional website URL
    """

    vendor_id: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-z0-9][a-z0-9\-]*$",
        description="Unique vendor identifier",
    )
    company_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Company display name",
    )
    public_key_pem: str = Field(
        ...,
        description="PEM-encoded ECDSA public key",
    )
    contact_email: str = Field(
        ...,
        description="Contact email address",
    )
    website: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Company website URL",
    )
