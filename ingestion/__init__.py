"""Ingestion front-door utilities for the drop-in URL/PDF/file workflow."""

from ingestion.shape_detector import detect_shape, ShapeReport

__all__ = ["detect_shape", "ShapeReport"]
