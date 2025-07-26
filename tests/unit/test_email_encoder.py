"""Unit tests for the email_encoder module."""

import base64

import pytest

from rxiv_maker.utils.email_encoder import (
    decode_email,
    encode_author_emails,
    encode_email,
    process_author_emails,
)


class TestEmailEncoder:
    """Test email encoding/decoding functionality."""

    def test_encode_email_valid(self):
        """Test encoding a valid email address."""
        email = "test@example.com"
        encoded = encode_email(email)

        # Verify it's base64 encoded
        assert encoded == base64.b64encode(email.encode()).decode()

        # Verify we can decode it back
        decoded = base64.b64decode(encoded).decode()
        assert decoded == email

    def test_encode_email_invalid(self):
        """Test encoding invalid email addresses."""
        with pytest.raises(ValueError):
            encode_email("invalid-email")

        with pytest.raises(ValueError):
            encode_email("@example.com")

        with pytest.raises(ValueError):
            encode_email("test@")

        with pytest.raises(ValueError):
            encode_email("")

        with pytest.raises(ValueError):
            encode_email(None)

    def test_decode_email_valid(self):
        """Test decoding a valid base64 encoded email."""
        email = "test@example.com"
        encoded = base64.b64encode(email.encode()).decode()

        decoded = decode_email(encoded)
        assert decoded == email

    def test_decode_email_invalid(self):
        """Test decoding invalid base64 strings."""
        with pytest.raises(ValueError):
            decode_email("invalid-base64")

        with pytest.raises(ValueError):
            decode_email("")

        with pytest.raises(ValueError):
            decode_email(None)

        # Test decoding valid base64 that's not an email
        invalid_email_b64 = base64.b64encode(b"not-an-email").decode()
        with pytest.raises(ValueError):
            decode_email(invalid_email_b64)

    def test_process_author_emails_with_email64(self):
        """Test processing authors with email64 fields."""
        authors = [
            {
                "name": "John Doe",
                "email64": base64.b64encode(b"john@example.com").decode(),
            },
            {
                "name": "Jane Smith",
                "email": "jane@example.com",  # Regular email unchanged
            },
        ]

        processed = process_author_emails(authors)

        # First author should have email64 decoded to email
        assert processed[0]["name"] == "John Doe"
        assert processed[0]["email"] == "john@example.com"
        assert "email64" not in processed[0]

        # Second author should have email unchanged
        assert processed[1]["name"] == "Jane Smith"
        assert processed[1]["email"] == "jane@example.com"
        assert "email64" not in processed[1]

    def test_process_author_emails_with_both_email_and_email64(self):
        """Test processing authors with both email and email64 fields."""
        authors = [
            {
                "name": "John Doe",
                "email": "old@example.com",
                "email64": base64.b64encode(b"new@example.com").decode(),
            }
        ]

        processed = process_author_emails(authors)

        # email64 should take precedence
        assert processed[0]["name"] == "John Doe"
        assert processed[0]["email"] == "new@example.com"
        assert "email64" not in processed[0]

    def test_process_author_emails_invalid_email64(self):
        """Test processing authors with invalid email64 fields."""
        authors = [{"name": "John Doe", "email64": "invalid-base64"}]

        processed = process_author_emails(authors)

        # Should remove invalid email64 field and not add email
        assert processed[0]["name"] == "John Doe"
        assert "email" not in processed[0]
        assert "email64" not in processed[0]

    def test_process_author_emails_empty_list(self):
        """Test processing empty author list."""
        authors = []
        processed = process_author_emails(authors)
        assert processed == []

    def test_process_author_emails_none(self):
        """Test processing None as authors."""
        processed = process_author_emails(None)
        assert processed is None

    def test_encode_author_emails(self):
        """Test encoding author emails to base64."""
        authors = [
            {"name": "John Doe", "email": "john@example.com"},
            {
                "name": "Jane Smith",
                "email64": base64.b64encode(b"jane@example.com").decode(),
            },
        ]

        processed = encode_author_emails(authors)

        # First author should have email encoded to email64
        assert processed[0]["name"] == "John Doe"
        expected_encoded = base64.b64encode(b"john@example.com").decode()
        assert processed[0]["email64"] == expected_encoded
        assert "email" not in processed[0]

        # Second author should remain unchanged (already has email64)
        assert processed[1]["name"] == "Jane Smith"
        expected_jane = base64.b64encode(b"jane@example.com").decode()
        assert processed[1]["email64"] == expected_jane
        assert "email" not in processed[1]

    def test_encode_author_emails_invalid_email(self):
        """Test encoding invalid email addresses."""
        authors = [{"name": "John Doe", "email": "invalid-email"}]

        processed = encode_author_emails(authors)

        # Should keep original email field if encoding fails
        assert processed[0]["name"] == "John Doe"
        assert processed[0]["email"] == "invalid-email"
        assert "email64" not in processed[0]
