"""Check who signed an Aadhaar Secure QR code. UIDAI publishes the certificates of the keys it signs with; this
module holds them (the "key ring") and says which of them, if any, made a code's signature.

The check is the whole of the code's worth: anyone can draw a QR code that says "born in 1990", but only UIDAI's
private key can make the 256 bytes that these public keys accept for it.
"""

from __future__ import annotations

from pathlib import Path

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

# UIDAI's "offline public key" certificates, as downloaded from uidai.gov.in → Build with us → Developer resources →
# Data and downloads, "Paperless Offline e-KYC and Secure QR Code" (their fingerprints are in docs/reports).
UIDAI_KEYS = Path(__file__).parent / "uidai_keys"
PEM_START = b"-----BEGIN"


class KeyRing:
    """The public keys a Secure QR may be signed with, each under its certificate's file name. A certificate that has
    run out stays on the ring on purpose: a card printed in 2020 was signed with 2020's key and is not printed again
    when that certificate ends. What counts is that the key was UIDAI's."""

    def __init__(self, folder: Path) -> None:
        self.keys: dict[str, rsa.RSAPublicKey] = {}
        for path in sorted(folder.glob("*.cer")):
            data = path.read_bytes()
            load = x509.load_pem_x509_certificate if data.startswith(PEM_START) else x509.load_der_x509_certificate
            key = load(data).public_key()
            if not isinstance(key, rsa.RSAPublicKey):
                raise ValueError(f"{path.name} doesn't hold an RSA key")
            self.keys[path.stem] = key

    def signer(self, signed: bytes, signature: bytes) -> str | None:
        """The name of the key that made `signature` over `signed`; None if none on the ring did."""
        for name, key in self.keys.items():
            try:
                key.verify(signature, signed, padding.PKCS1v15(), hashes.SHA256())
            except InvalidSignature:
                continue
            return name
        return None
