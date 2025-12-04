import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from loguru import logger


class OTPManager:
    """Manages OTP generation and validation with in-memory storage"""

    def __init__(self, expiry_minutes: int = 10):
        self.expiry_minutes = expiry_minutes
        self._sessions: Dict[int, Dict[str, Any]] = {}

    def generate_otp(self, length: int = 6) -> str:
        """Generate a secure numeric OTP"""
        return "".join(secrets.choice(string.digits) for _ in range(length))

    def create_session(
        self,
        telegram_id: int,
        employee_id: int,
        employee_email: str,
    ) -> str:
        """Create a verification session and return the OTP"""
        otp = self.generate_otp()
        now = datetime.now()

        self._sessions[telegram_id] = {
            "employee_id": employee_id,
            "employee_email": employee_email,
            "otp_code": otp,
            "created_at": now,
            "expires_at": now + timedelta(minutes=self.expiry_minutes),
            "attempts": 0,
        }

        logger.info(f"Created OTP session for telegram_id={telegram_id}")
        return otp

    def verify_otp(self, telegram_id: int, otp: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verify OTP for a telegram user.
        Returns (success, session_data) tuple.
        """
        session = self._sessions.get(telegram_id)

        if not session:
            logger.warning(f"No session found for telegram_id={telegram_id}")
            return False, None

        # Check expiry
        if datetime.now() > session["expires_at"]:
            logger.warning(f"OTP expired for telegram_id={telegram_id}")
            self.clear_session(telegram_id)
            return False, None

        # Increment attempts
        session["attempts"] += 1

        # Max 3 attempts
        if session["attempts"] > 3:
            logger.warning(f"Max OTP attempts exceeded for telegram_id={telegram_id}")
            self.clear_session(telegram_id)
            return False, None

        # Verify OTP
        if secrets.compare_digest(session["otp_code"], otp):
            logger.info(f"OTP verified successfully for telegram_id={telegram_id}")
            session_data = {
                "employee_id": session["employee_id"],
                "employee_email": session["employee_email"],
            }
            self.clear_session(telegram_id)
            return True, session_data

        logger.warning(f"Invalid OTP attempt {session['attempts']}/3 for telegram_id={telegram_id}")
        return False, None

    def get_session(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get session data without OTP code"""
        session = self._sessions.get(telegram_id)
        if session:
            return {
                "employee_id": session["employee_id"],
                "employee_email": session["employee_email"],
                "expires_at": session["expires_at"],
                "attempts": session["attempts"],
            }
        return None

    def clear_session(self, telegram_id: int) -> None:
        """Clear a verification session"""
        if telegram_id in self._sessions:
            del self._sessions[telegram_id]
            logger.info(f"Cleared OTP session for telegram_id={telegram_id}")

    def cleanup_expired(self) -> int:
        """Remove all expired sessions. Returns count of removed sessions."""
        now = datetime.now()
        expired = [
            tid for tid, session in self._sessions.items()
            if now > session["expires_at"]
        ]
        for tid in expired:
            del self._sessions[tid]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired OTP sessions")
        return len(expired)


# Global OTP manager instance
otp_manager = OTPManager()
