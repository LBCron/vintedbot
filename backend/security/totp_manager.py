"""
Mobile App Security: TOTP-based Two-Factor Authentication (2FA)
Implements TOTP (Time-based One-Time Password) for enhanced security
"""
import pyotp
import qrcode
import io
import base64
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class TOTPSetup:
    """2FA setup data"""
    secret: str
    qr_code_data: str  # Base64-encoded QR code image
    backup_codes: list[str]
    provisioning_uri: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'secret': self.secret,
            'qr_code': self.qr_code_data,
            'backup_codes': self.backup_codes,
            'provisioning_uri': self.provisioning_uri
        }


class TOTPManager:
    """
    TOTP-based 2FA Manager

    Features:
    - TOTP secret generation
    - QR code generation for authenticator apps
    - Code verification (6-digit codes)
    - Backup codes
    - Window tolerance for time drift
    """

    # TOTP configuration
    INTERVAL = 30  # 30 seconds per code
    DIGITS = 6     # 6-digit codes
    ALGORITHM = 'sha1'  # Standard TOTP uses SHA1

    # Verification window (allows codes from ±1 interval for clock skew)
    VALID_WINDOW = 1

    # Backup codes
    BACKUP_CODE_COUNT = 10
    BACKUP_CODE_LENGTH = 8

    def __init__(self, issuer_name: str = "VintedBot"):
        """
        Initialize TOTP manager

        Args:
            issuer_name: Name to display in authenticator apps
        """
        self.issuer_name = issuer_name

    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret

        Returns:
            Base32-encoded secret
        """
        secret = pyotp.random_base32()
        logger.debug(f"Generated new TOTP secret")
        return secret

    def generate_backup_codes(self, count: int = BACKUP_CODE_COUNT) -> list[str]:
        """
        Generate backup codes for account recovery

        Args:
            count: Number of backup codes to generate

        Returns:
            List of backup codes
        """
        codes = []

        for _ in range(count):
            # Generate random alphanumeric code
            code = pyotp.random_base32(length=self.BACKUP_CODE_LENGTH)
            # Format as XXXX-XXXX for readability
            formatted = f"{code[:4]}-{code[4:8]}"
            codes.append(formatted)

        logger.debug(f"Generated {count} backup codes")
        return codes

    def create_qr_code(self, secret: str, account_name: str) -> str:
        """
        Create QR code for authenticator app setup

        Args:
            secret: TOTP secret
            account_name: User's account identifier (usually email)

        Returns:
            Base64-encoded PNG image of QR code
        """
        # Create TOTP URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=account_name,
            issuer_name=self.issuer_name
        )

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        qr_code_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        logger.debug(f"Generated QR code for {account_name}")
        return qr_code_data

    def setup_2fa(self, user_email: str) -> TOTPSetup:
        """
        Complete 2FA setup for a user

        Args:
            user_email: User's email address

        Returns:
            TOTPSetup with secret, QR code, and backup codes
        """
        # Generate secret
        secret = self.generate_secret()

        # Generate QR code
        qr_code = self.create_qr_code(secret, user_email)

        # Generate backup codes
        backup_codes = self.generate_backup_codes()

        # Create provisioning URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=self.issuer_name
        )

        logger.info(f"2FA setup completed for {user_email}")

        return TOTPSetup(
            secret=secret,
            qr_code_data=qr_code,
            backup_codes=backup_codes,
            provisioning_uri=provisioning_uri
        )

    def verify_code(
        self,
        secret: str,
        code: str,
        window: int = VALID_WINDOW
    ) -> bool:
        """
        Verify a TOTP code

        Args:
            secret: User's TOTP secret
            code: 6-digit code to verify
            window: Time window tolerance (default ±1 interval = ±30s)

        Returns:
            True if code is valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(secret)

            # Verify code with time window
            is_valid = totp.verify(code, valid_window=window)

            if is_valid:
                logger.info("TOTP code verified successfully")
            else:
                logger.warning("Invalid TOTP code")

            return is_valid

        except Exception as e:
            logger.error(f"TOTP verification failed: {e}")
            return False

    def get_current_code(self, secret: str) -> str:
        """
        Get current TOTP code (for testing)

        Args:
            secret: TOTP secret

        Returns:
            Current 6-digit code
        """
        totp = pyotp.TOTP(secret)
        return totp.now()

    def verify_backup_code(
        self,
        provided_code: str,
        valid_backup_codes: list[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a backup code

        Args:
            provided_code: Code provided by user
            valid_backup_codes: List of unused backup codes

        Returns:
            (is_valid, used_code) - used_code should be removed from valid list
        """
        # Normalize input (remove dashes, uppercase)
        normalized_input = provided_code.replace('-', '').upper()

        for backup_code in valid_backup_codes:
            normalized_backup = backup_code.replace('-', '').upper()

            if normalized_input == normalized_backup:
                logger.info("Backup code verified successfully")
                return (True, backup_code)

        logger.warning("Invalid backup code")
        return (False, None)


# Singleton instance
_totp_manager: Optional[TOTPManager] = None


def get_totp_manager() -> TOTPManager:
    """Get global TOTP manager instance"""
    global _totp_manager
    if _totp_manager is None:
        _totp_manager = TOTPManager(issuer_name="VintedBot")
    return _totp_manager


# Storage helpers (would be in database in production)
class TOTPStorage:
    """In-memory storage for 2FA data (use database in production)"""

    def __init__(self):
        # user_id → {secret, backup_codes, enabled}
        self.user_2fa: Dict[int, Dict[str, Any]] = {}

    def enable_2fa(
        self,
        user_id: int,
        secret: str,
        backup_codes: list[str]
    ):
        """Enable 2FA for user"""
        self.user_2fa[user_id] = {
            'secret': secret,
            'backup_codes': backup_codes.copy(),
            'enabled': True
        }
        logger.info(f"2FA enabled for user {user_id}")

    def disable_2fa(self, user_id: int):
        """Disable 2FA for user"""
        if user_id in self.user_2fa:
            del self.user_2fa[user_id]
            logger.info(f"2FA disabled for user {user_id}")

    def is_2fa_enabled(self, user_id: int) -> bool:
        """Check if 2FA is enabled"""
        return user_id in self.user_2fa and self.user_2fa[user_id].get('enabled', False)

    def get_secret(self, user_id: int) -> Optional[str]:
        """Get user's TOTP secret"""
        return self.user_2fa.get(user_id, {}).get('secret')

    def get_backup_codes(self, user_id: int) -> list[str]:
        """Get user's remaining backup codes"""
        return self.user_2fa.get(user_id, {}).get('backup_codes', [])

    def use_backup_code(self, user_id: int, code: str) -> bool:
        """Mark a backup code as used"""
        if user_id not in self.user_2fa:
            return False

        backup_codes = self.user_2fa[user_id].get('backup_codes', [])

        if code in backup_codes:
            backup_codes.remove(code)
            logger.info(f"Backup code used for user {user_id}, {len(backup_codes)} remaining")
            return True

        return False


# Global storage instance
_totp_storage = TOTPStorage()


def get_totp_storage() -> TOTPStorage:
    """Get global TOTP storage"""
    return _totp_storage


# High-level 2FA functions for API endpoints
async def enable_2fa_for_user(user_id: int, user_email: str) -> TOTPSetup:
    """
    Enable 2FA for a user (complete flow)

    Args:
        user_id: User ID
        user_email: User email

    Returns:
        TOTPSetup with QR code and backup codes
    """
    manager = get_totp_manager()
    storage = get_totp_storage()

    # Generate 2FA setup
    setup = manager.setup_2fa(user_email)

    # Store in database (for now, in-memory)
    storage.enable_2fa(user_id, setup.secret, setup.backup_codes)

    logger.info(f"2FA enabled for user {user_id}")

    return setup


async def verify_2fa_code(user_id: int, code: str) -> bool:
    """
    Verify 2FA code for a user

    Args:
        user_id: User ID
        code: 6-digit TOTP code or backup code

    Returns:
        True if valid
    """
    manager = get_totp_manager()
    storage = get_totp_storage()

    if not storage.is_2fa_enabled(user_id):
        logger.warning(f"2FA not enabled for user {user_id}")
        return False

    # Try TOTP code first
    secret = storage.get_secret(user_id)
    if secret and manager.verify_code(secret, code):
        return True

    # Try backup code
    backup_codes = storage.get_backup_codes(user_id)
    is_valid, used_code = manager.verify_backup_code(code, backup_codes)

    if is_valid and used_code:
        storage.use_backup_code(user_id, used_code)
        return True

    return False


async def disable_2fa_for_user(user_id: int):
    """Disable 2FA for a user"""
    storage = get_totp_storage()
    storage.disable_2fa(user_id)
    logger.info(f"2FA disabled for user {user_id}")


if __name__ == "__main__":
    # Test TOTP manager
    print("Testing TOTP manager...")

    manager = TOTPManager(issuer_name="VintedBot")

    # Setup 2FA
    setup = manager.setup_2fa("test@example.com")

    print(f"\nSecret: {setup.secret}")
    print(f"QR Code (base64): {setup.qr_code_data[:50]}...")
    print(f"Backup Codes: {setup.backup_codes}")

    # Get current code
    current_code = manager.get_current_code(setup.secret)
    print(f"\nCurrent Code: {current_code}")

    # Verify code
    is_valid = manager.verify_code(setup.secret, current_code)
    print(f"Code Valid: {is_valid}")

    # Test backup code
    backup_valid, used = manager.verify_backup_code(setup.backup_codes[0], setup.backup_codes)
    print(f"Backup Code Valid: {backup_valid}, Used: {used}")

    print("\n✅ TOTP manager test passed!")
