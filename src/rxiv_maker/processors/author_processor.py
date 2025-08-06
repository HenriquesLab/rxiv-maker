"""Author information processing utilities for Rxiv-Maker.

This module handles the generation of LaTeX author information sections,
including authors and affiliations, corresponding authors, and extended author info.
"""


def generate_authors_and_affiliations(yaml_metadata):
    """Generate LaTeX author and affiliation blocks from YAML metadata."""
    authors_latex = []
    affiliations_latex = []

    # Extract authors and affiliations from metadata
    authors = yaml_metadata.get("authors", [])
    affiliations = yaml_metadata.get("affiliations", [])

    if not authors:
        # Fallback to default if no authors specified
        return (
            "% Use letters for affiliations, numbers to show equal "
            "authorship (if applicable) and to indicate the corresponding author\n"
            "\\author[1]{Author Name}\n"
            "\\affil[1]{Institution}"
        )

    # Create affiliations mapping from shortname to number and full details
    affil_map = {}
    used_affiliations = []  # Keep order of first appearance

    # First pass: collect all unique affiliations used by authors in order of appearance
    for author in authors:
        if isinstance(author, dict):
            author_affiliations = author.get("affiliations", [])
            for affil_short in author_affiliations:
                if affil_short not in used_affiliations:
                    used_affiliations.append(affil_short)

    # Create mapping and LaTeX for used affiliations in order of appearance
    for i, affil_short in enumerate(used_affiliations, 1):
        affil_map[affil_short] = i

        # Find full affiliation details
        full_affil = affil_short  # fallback to shortname
        for affil_detail in affiliations:
            if isinstance(affil_detail, dict) and affil_detail.get("shortname") == affil_short:
                full_name = affil_detail.get("full_name", affil_short)
                location = affil_detail.get("location", "")
                full_affil = f"{full_name}, {location}" if location else full_name
                break

        affiliations_latex.append(f"\\affil[{i}]{{{full_affil}}}")

    # Create authors with proper affiliation mapping
    corresponding_authors = []
    equal_contributors = []

    for author in authors:
        if isinstance(author, dict):
            name = author.get("name", "Unknown Author")
            author_affiliations = author.get("affiliations", [])
            is_corresponding = author.get("corresponding_author", False)
            is_equal = author.get("co_first_author", False)

            # Map author affiliations to numbers and sort them
            affil_numbers = []
            for affil in author_affiliations:
                if affil in affil_map:
                    affil_numbers.append(affil_map[affil])

            # Sort affiliation numbers for each author
            affil_numbers.sort()

            # Format affiliations for author
            affil_str = ",".join(map(str, affil_numbers)) if affil_numbers else "1"  # Default to first affiliation

            # Add special markers
            special_markers = []
            if is_equal:
                special_markers.append("*")
                equal_contributors.append(name)
            if is_corresponding:
                special_markers.append("\\Letter")
                corresponding_authors.append(name)

            if special_markers:
                affil_str += "," + ",".join(special_markers)

            authors_latex.append(f"\\author[{affil_str}]{{{name}}}")
        elif isinstance(author, str):
            authors_latex.append(f"\\author[1]{{{author}}}")

    # Add special affiliations for equal contributors
    if equal_contributors:
        affiliations_latex.append("\\affil[*]{Equally contributed authors}")

    # Combine all parts
    result = "% Authors and affiliations generated from metadata\n"
    result += "\n".join(authors_latex)
    result += "\n"
    result += "\n".join(affiliations_latex)

    return result


def generate_corresponding_authors(yaml_metadata):
    """Generate LaTeX corresponding authors section from YAML metadata."""
    authors = yaml_metadata.get("authors", [])

    if not authors:
        return "% No corresponding authors found\n"

    corresponding_authors = []

    for author in authors:
        if isinstance(author, dict):
            # Check if this author is marked as corresponding author
            is_corresponding = author.get("corresponding_author", False)

            if is_corresponding:
                name = author.get("name", "Unknown Author")
                email = author.get("email", "")

                # Generate abbreviated name (first letter of first and middle
                # names, then last name)
                name_parts = name.split()
                if len(name_parts) >= 2:
                    # Get first letters of all names except the last one
                    initials = [part[0].upper() for part in name_parts[:-1]]
                    last_name = name_parts[-1]
                    abbreviated_name = ". ".join(initials) + ". " + last_name
                else:
                    abbreviated_name = name

                # Format contact information
                contact_info = []
                if email:
                    # Convert @ to \at for LaTeX
                    email_tex = email.replace("@", "\\at ")
                    contact_info.append(email_tex)
                # Note: Bluesky handles excluded from corresponding authors section

                if contact_info:
                    contact_str = "; ".join(contact_info)
                    corresponding_authors.append(f"({abbreviated_name}) {contact_str}")
                else:
                    # If no contact info, just include the abbreviated name
                    corresponding_authors.append(f"({abbreviated_name})")

    if corresponding_authors:
        result = "\\begin{corrauthor}\n"
        result += "; \n".join(corresponding_authors)
        result += "\n\\end{corrauthor}"
        return result
    else:
        return "% No corresponding authors found\n"


def generate_extended_author_info(yaml_metadata):
    """Generate LaTeX extended author information section from YAML metadata."""
    authors = yaml_metadata.get("authors", [])

    if not authors:
        return "% No authors found for extended author information\n"

    def escape_latex_special_chars(text):
        """Escape special LaTeX characters in text."""
        # Replace common special characters that need escaping in LaTeX
        text = text.replace("_", "\\_")
        text = text.replace("&", "\\&")
        text = text.replace("%", "\\%")
        text = text.replace("#", "\\#")
        text = text.replace("{", "\\{")
        text = text.replace("}", "\\}")
        return text

    result = "\\begin{extendedauthorlist}\n"

    author_items = []

    for author in authors:
        if isinstance(author, dict):
            name = author.get("name", "Unknown Author")
            orcid = author.get("orcid", "")

            # Social media handles
            twitter = author.get("twitter", "")
            x = author.get("x", "")
            bluesky = author.get("bluesky", "")
            linkedin = author.get("linkedin", "")

            # Check if author has any extended information
            has_extended_info = any([orcid, twitter, x, bluesky, linkedin])

            # Only include authors with extended information
            if not has_extended_info:
                continue

            # Build the social media line
            social_icons = []

            # Add ORCID if available
            if orcid:
                # Remove any https://orcid.org/ prefix if present
                orcid_clean = orcid.replace("https://orcid.org/", "").replace("http://orcid.org/", "")
                social_icons.append(f"\\orcidicon{{{orcid_clean}}}")

            # Prefer X over Twitter if both are present
            if x:
                # Clean X handle (remove @ if present)
                x_clean = x.replace("@", "").replace("https://x.com/", "").replace("http://x.com/", "")
                x_clean = escape_latex_special_chars(x_clean)
                social_icons.append(f"\\xicon{{{x_clean}}}")
            elif twitter:
                # Clean Twitter handle (remove @ if present)
                twitter_clean = (
                    twitter.replace("@", "").replace("https://twitter.com/", "").replace("http://twitter.com/", "")
                )
                twitter_clean = escape_latex_special_chars(twitter_clean)
                social_icons.append(f"\\twittericon{{{twitter_clean}}}")

            if bluesky:
                # Clean Bluesky handle (remove @ if present)
                bluesky_clean = (
                    bluesky.replace("@", "")
                    .replace("https://bsky.app/profile/", "")
                    .replace("http://bsky.app/profile/", "")
                )
                bluesky_clean = escape_latex_special_chars(bluesky_clean)
                social_icons.append(f"\\blueskyicon{{{bluesky_clean}}}")

            if linkedin:
                # Clean LinkedIn handle
                linkedin_clean = linkedin.replace("https://linkedin.com/in/", "").replace("http://linkedin.com/in/", "")
                linkedin_clean = escape_latex_special_chars(linkedin_clean)
                social_icons.append(f"\\linkedinicon{{{linkedin_clean}}}")

            # Create social media line
            social_line = "; ".join(social_icons) if social_icons else ""

            # Use the new extendedauthor command
            author_items.append(f"\\extendedauthor{{{name}}}{{{social_line}}}")

    result += "\n".join(author_items)
    result += "\n\\end{extendedauthorlist}"

    return result
