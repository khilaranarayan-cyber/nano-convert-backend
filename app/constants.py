# app/constants.py
# Tools metadata (translated from provided JSON). Centralized TOOLS_META used across the app.

from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class ToolOption(BaseModel):
    name: str
    type: str  # 'number' | 'string' | 'enum' | 'boolean'
    description: Optional[str] = None
    enumValues: Optional[List[str]] = None


class ToolMeta(BaseModel):
    slug: str
    name: str
    category: str  # 'pdf' | 'image'
    description: Optional[str]
    heavy: bool
    maxInputFiles: int
    maxSizeBytes: Optional[int]
    allowedMimeTypes: List[str]
    options: Optional[Dict[str, ToolOption]] = None


TOOLS_META: Dict[str, ToolMeta] = {
    # PDF tools
    "merge-pdf": ToolMeta(
        slug="merge-pdf",
        name="Merge PDF",
        category="pdf",
        description="Merge multiple PDFs into one",
        heavy=True,
        maxInputFiles=20,
        maxSizeBytes=200 * 1024 * 1024,
        allowedMimeTypes=["application/pdf"],
    ),
    "split-pdf": ToolMeta(
        slug="split-pdf",
        name="Split PDF",
        category="pdf",
        description=None,
        heavy=True,
        maxInputFiles=1,
        allowedMimeTypes=["application/pdf"],
    ),
    "compress-pdf": ToolMeta(
        slug="compress-pdf",
        name="Compress PDF",
        category="pdf",
        description=None,
        heavy=True,
        maxInputFiles=1,
        allowedMimeTypes=["application/pdf"],
    ),
    "pdf-resize-size": ToolMeta(
        slug="pdf-resize-size",
        name="PDF Resize (KB/MB)",
        category="pdf",
        description=None,
        heavy=True,
        maxInputFiles=1,
        allowedMimeTypes=["application/pdf"],
    ),
    "pdf-to-image": ToolMeta(
        slug="pdf-to-image",
        name="PDF to Image",
        category="pdf",
        description=None,
        heavy=True,
        maxInputFiles=1,
        allowedMimeTypes=["application/pdf"],
    ),
    "image-to-pdf": ToolMeta(
        slug="image-to-pdf",
        name="Image to PDF",
        category="pdf",
        description=None,
        heavy=False,
        maxInputFiles=20,
        allowedMimeTypes=["image/jpeg", "image/png", "image/webp"],
    ),
    "rotate-pdf": ToolMeta(
        slug="rotate-pdf",
        name="Rotate PDF",
        category="pdf",
        description=None,
        heavy=False,
        maxInputFiles=1,
        allowedMimeTypes=["application/pdf"],
    ),
    "delete-pages": ToolMeta(
        slug="delete-pages",
        name="Delete Pages",
        category="pdf",
        description=None,
        heavy=False,
        maxInputFiles=1,
        allowedMimeTypes=["application/pdf"],
    ),
    "extract-pages": ToolMeta(
        slug="extract-pages",
        name="Extract Pages",
        category="pdf",
        description=None,
        heavy=False,
        maxInputFiles=1,
        allowedMimeTypes=["application/pdf"],
    ),
    "add-watermark": ToolMeta(
        slug="add-watermark",
        name="Add Watermark",
        category="pdf",
        description=None,
        heavy=False,
        maxInputFiles=1,
        allowedMimeTypes=["application/pdf", "image/png", "image/jpeg"],
    ),
    # Image tools
    "image-compressor": ToolMeta(
        slug="image-compressor",
        name="Image Compressor",
        category="image",
        description=None,
        heavy=True,
        maxInputFiles=1,
        allowedMimeTypes=["image/jpeg", "image/png", "image/webp"],
    ),
    "image-resize-kb": ToolMeta(
        slug="image-resize-kb",
        name="Image Resizer (KB / MB)",
        category="image",
        description=None,
        heavy=True,
        maxInputFiles=1,
        allowedMimeTypes=["image/jpeg", "image/png", "image/webp"],
    ),
    "image-resize-dim": ToolMeta(
        slug="image-resize-dim",
        name="Image Resizer (Dimensions)",
        category="image",
        description=None,
        heavy=False,
        maxInputFiles=1,
        allowedMimeTypes=["image/jpeg", "image/png", "image/webp"],
    ),
    "crop-image": ToolMeta(
        slug="crop-image",
        name="Crop Image",
        category="image",
        description=None,
        heavy=False,
        maxInputFiles=1,
        allowedMimeTypes=["image/jpeg", "image/png", "image/webp"],
    ),
    "convert-image": ToolMeta(
        slug="convert-image",
        name="Convert Image (JPG / PNG / WEBP)",
        category="image",
        description=None,
        heavy=False,
        maxInputFiles=1,
        allowedMimeTypes=["image/jpeg", "image/png", "image/webp"],
    ),
    "rotate-image": ToolMeta(
        slug="rotate-image",
        name="Rotate Image",
        category="image",
        description=None,
        heavy=False,
        maxInputFiles=1,
        allowedMimeTypes=["image/jpeg", "image/png", "image/webp"],
    ),
    "flip-image": ToolMeta(
        slug="flip-image",
        name="Flip Image",
        category="image",
        description=None,
        heavy=False,
        maxInputFiles=1,
        allowedMimeTypes=["image/jpeg", "image/png", "image/webp"],
    ),
    "image-watermark": ToolMeta(
        slug="image-watermark",
        name="Image Watermark",
        category="image",
        description=None,
        heavy=False,
        maxInputFiles=1,
        allowedMimeTypes=["image/jpeg", "image/png", "image/webp"],
    ),
    "merge-images": ToolMeta(
        slug="merge-images",
        name="Merge Images",
        category="image",
        description=None,
        heavy=True,
        maxInputFiles=20,
        allowedMimeTypes=["image/jpeg", "image/png", "image/webp"],
    ),
    "split-image-grid": ToolMeta(
        slug="split-image-grid",
        name="Split Image (Grid)",
        category="image",
        description=None,
        heavy=True,
        maxInputFiles=1,
        allowedMimeTypes=["image/jpeg", "image/png", "image/webp"],
    ),
}
