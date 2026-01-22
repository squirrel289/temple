"""
TokenCleaningService - Strips template tokens for base format linting
"""

from typing import Tuple, List
from temple.template_tokenizer import temple_tokenizer, Token


class TokenCleaningService:
    """
    Service responsible for stripping template tokens and tracking text positions.

    This service:
    - Tokenizes template content
    - Extracts only text tokens (strips DSL tokens)
    - Tracks original positions for diagnostic mapping
    """

    def clean_text_and_tokens(self, text: str) -> Tuple[str, List[Token]]:
        """
        Strip template tokens and return cleaned text with position tracking.

        Args:
            text: Original template content

        Returns:
            Tuple of (cleaned_text, text_tokens)
            - cleaned_text: Content with all DSL tokens removed
            - text_tokens: List of text Token objects for position mapping
        """
        text_tokens: List[Token] = []
        cleaned_chars: List[str] = []

        for token in temple_tokenizer(text):
            if token.type == "text":
                text_tokens.append(token)
                cleaned_chars.append(token.value)

        cleaned_text = "".join(cleaned_chars)
        return cleaned_text, text_tokens
