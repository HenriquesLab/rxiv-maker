"""Email encoding/decoding utilities for Rxiv-Maker.

This module handles the encoding of email addresses to base64 for privacy in YAML files
and their decoding for use in PDF generation.
"""

import base64
import re


def encode_email(email):
    """Encode an email address to base64.

    Args:
        email (str): The email address to encode

    Returns:
        str: Base64 encoded email address

    Raises:
        ValueError: If the email format is invalid
    """
    if not email or not isinstance(email, str):
        raise ValueError("Email must be a non-empty string")

    # Basic email validation
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email.strip()):
        raise ValueError(f"Invalid email format: {email}")

    # Encode the email to base64
    email_bytes = email.strip().encode("utf-8")
    encoded_email = base64.b64encode(email_bytes).decode("utf-8")

    return encoded_email


def decode_email(encoded_email):
    """Decode a base64 encoded email address.

    Args:
        encoded_email (str): The base64 encoded email address

    Returns:
        str: Decoded email address

    Raises:
        ValueError: If the encoded email is invalid or cannot be decoded
    """
    if not encoded_email or not isinstance(encoded_email, str):
        raise ValueError("Encoded email must be a non-empty string")

    try:
        # Decode from base64
        decoded_bytes = base64.b64decode(encoded_email.strip())
        decoded_email = decoded_bytes.decode("utf-8")

        # Validate the decoded email
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, decoded_email):
            raise ValueError(f"Decoded string is not a valid email: {decoded_email}")

        return decoded_email

    except (base64.binascii.Error, UnicodeDecodeError) as e:
        raise ValueError(f"Invalid base64 encoded email: {encoded_email}") from e


def process_author_emails(authors):
    """Process author list to decode any base64 encoded emails.

    This function looks for 'email64' fields in author entries and converts them
    to regular 'email' fields with decoded values. Regular 'email' fields are
    left unchanged.

    Args:
        authors (list): List of author dictionaries

    Returns:
        list: List of author dictionaries with decoded emails
    """
    if not isinstance(authors, list):
        return authors

    processed_authors = []

    for author in authors:
        if not isinstance(author, dict):
            processed_authors.append(author)
            continue

        # Create a copy to avoid modifying the original
        processed_author = author.copy()

        # Only process email64 fields - leave regular email fields unchanged
        if "email64" in processed_author:
            try:
                # Decode the email
                decoded_email = decode_email(processed_author["email64"])
                processed_author["email"] = decoded_email

                # Remove the email64 field to avoid confusion
                del processed_author["email64"]

            except ValueError as e:
                author_name = processed_author.get("name", "Unknown")
                print(f"Warning: Failed to decode email64 for author {author_name}: {e}")
                # If decoding fails, remove the email64 field but don't add email
                del processed_author["email64"]

        # If author has both email and email64, email64 takes precedence
        # and email is overwritten. Regular email fields are left as-is

        processed_authors.append(processed_author)

    return processed_authors


def encode_author_emails(authors):
    """Process author list to encode emails to base64.

    This function looks for 'email' fields in author entries and converts them
    to 'email64' fields with encoded values.

    Args:
        authors (list): List of author dictionaries

    Returns:
        list: List of author dictionaries with encoded emails
    """
    if not isinstance(authors, list):
        return authors

    processed_authors = []

    for author in authors:
        if not isinstance(author, dict):
            processed_authors.append(author)
            continue

        # Create a copy to avoid modifying the original
        processed_author = author.copy()

        # Check if author has email field
        if "email" in processed_author and processed_author["email"]:
            try:
                # Encode the email
                encoded_email = encode_email(processed_author["email"])
                processed_author["email64"] = encoded_email

                # Remove the original email field
                del processed_author["email"]

            except ValueError as e:
                author_name = processed_author.get("name", "Unknown")
                print(f"Warning: Failed to encode email for author {author_name}: {e}")
                # If encoding fails, keep the original email field

        processed_authors.append(processed_author)

    return processed_authors
