"""
Utility modules for the visa Q&A application.

Provides shared functionality for watermarking, validation, and common operations.
"""

from .watermark import (
    generate_post_watermarks,
    generate_comment_watermarks,
    generate_display_watermark,
    generate_legal_watermark,
    verify_watermark,
    parse_display_watermark
)

__all__ = [
    "generate_post_watermarks",
    "generate_comment_watermarks", 
    "generate_display_watermark",
    "generate_legal_watermark",
    "verify_watermark",
    "parse_display_watermark"
]