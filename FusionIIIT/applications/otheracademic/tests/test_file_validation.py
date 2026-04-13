"""
Tests for Bonafide file validation.
Tests file extension, size, and MIME type validation.
"""
import os
import tempfile
from io import BytesIO
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from applications.otheracademic.api.file_validation import (
    validate_file_extension,
    validate_file_size,
    validate_file_mime_type,
    validate_bonafide_file,
    FileValidationError,
    MAX_FILE_SIZE_MB,
)


class FileValidationTestCase(TestCase):
    """Test suite for file validation utilities."""

    def test_validate_file_extension_valid_pdf(self):
        """Test valid PDF extension."""
        extension = validate_file_extension("document.pdf")
        self.assertEqual(extension, "pdf")

    def test_validate_file_extension_valid_jpg(self):
        """Test valid JPG extension."""
        extension = validate_file_extension("photo.jpg")
        self.assertEqual(extension, "jpg")

    def test_validate_file_extension_valid_jpeg(self):
        """Test valid JPEG extension."""
        extension = validate_file_extension("image.jpeg")
        self.assertEqual(extension, "jpeg")

    def test_validate_file_extension_valid_png(self):
        """Test valid PNG extension."""
        extension = validate_file_extension("image.png")
        self.assertEqual(extension, "png")

    def test_validate_file_extension_case_insensitive(self):
        """Test extension validation is case-insensitive."""
        extension = validate_file_extension("document.PDF")
        self.assertEqual(extension, "pdf")

    def test_validate_file_extension_invalid(self):
        """Test invalid file extension raises error."""
        with self.assertRaises(FileValidationError) as context:
            validate_file_extension("document.exe")
        self.assertIn("not supported", str(context.exception))

    def test_validate_file_extension_no_extension(self):
        """Test file without extension raises error."""
        with self.assertRaises(FileValidationError) as context:
            validate_file_extension("document")
        self.assertIn("must have an extension", str(context.exception))

    def test_validate_file_size_within_limit(self):
        """Test file within size limit passes."""
        file = SimpleUploadedFile(
            "test.pdf",
            b"x" * (1024 * 1024),  # 1 MB
            content_type="application/pdf"
        )
        # Should not raise
        validate_file_size(file)

    def test_validate_file_size_exactly_at_limit(self):
        """Test file exactly at 5MB limit passes."""
        file = SimpleUploadedFile(
            "test.pdf",
            b"x" * (5 * 1024 * 1024),  # 5 MB
            content_type="application/pdf"
        )
        # Should not raise
        validate_file_size(file)

    def test_validate_file_size_exceeds_limit(self):
        """Test file exceeding size limit raises error."""
        file = SimpleUploadedFile(
            "test.pdf",
            b"x" * (6 * 1024 * 1024),  # 6 MB
            content_type="application/pdf"
        )
        with self.assertRaises(FileValidationError) as context:
            validate_file_size(file)
        self.assertIn("exceeds", str(context.exception))
        self.assertIn(f"{MAX_FILE_SIZE_MB} MB", str(context.exception))

    def test_validate_pdf_mime_type_valid(self):
        """Test valid PDF magic number."""
        # PDF magic number: %PDF
        pdf_content = b"%PDF-1.4\n%test content"
        file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )
        # Should not raise
        validate_file_mime_type(file, "pdf")

    def test_validate_pdf_mime_type_invalid(self):
        """Test invalid PDF magic number raises error."""
        # Invalid PDF content
        invalid_content = b"This is not a PDF file"
        file = SimpleUploadedFile(
            "test.pdf",
            invalid_content,
            content_type="application/pdf"
        )
        with self.assertRaises(FileValidationError) as context:
            validate_file_mime_type(file, "pdf")
        self.assertIn("does not match PDF format", str(context.exception))

    def test_validate_jpeg_mime_type_valid(self):
        """Test valid JPEG magic number."""
        # JPEG magic number: FFD8FF
        jpeg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01"
        file = SimpleUploadedFile(
            "test.jpg",
            jpeg_content,
            content_type="image/jpeg"
        )
        # Should not raise
        validate_file_mime_type(file, "jpg")

    def test_validate_jpeg_mime_type_invalid(self):
        """Test invalid JPEG magic number raises error."""
        invalid_content = b"Not a JPEG file"
        file = SimpleUploadedFile(
            "test.jpg",
            invalid_content,
            content_type="image/jpeg"
        )
        with self.assertRaises(FileValidationError) as context:
            validate_file_mime_type(file, "jpg")
        self.assertIn("does not match JPEG format", str(context.exception))

    def test_validate_png_mime_type_valid(self):
        """Test valid PNG magic number."""
        # PNG magic number: 89504E47 (in bytes: \x89PNG)
        png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        file = SimpleUploadedFile(
            "test.png",
            png_content,
            content_type="image/png"
        )
        # Should not raise
        validate_file_mime_type(file, "png")

    def test_validate_png_mime_type_invalid(self):
        """Test invalid PNG magic number raises error."""
        invalid_content = b"Not a PNG file"
        file = SimpleUploadedFile(
            "test.png",
            invalid_content,
            content_type="image/png"
        )
        with self.assertRaises(FileValidationError) as context:
            validate_file_mime_type(file, "png")
        self.assertIn("does not match PNG format", str(context.exception))

    def test_validate_bonafide_file_valid_pdf(self):
        """Test complete validation with valid PDF file."""
        pdf_content = b"%PDF-1.4\n%test content"
        file = SimpleUploadedFile(
            "bonafide.pdf",
            pdf_content,
            content_type="application/pdf"
        )
        result = validate_bonafide_file(file)
        self.assertTrue(result["valid"])
        self.assertIsNotNone(result["file_info"])
        self.assertEqual(result["file_info"]["extension"], "pdf")
        self.assertEqual(result["file_info"]["filename"], "bonafide.pdf")

    def test_validate_bonafide_file_valid_png(self):
        """Test complete validation with valid PNG file."""
        png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        file = SimpleUploadedFile(
            "bonafide.png",
            png_content,
            content_type="image/png"
        )
        result = validate_bonafide_file(file)
        self.assertTrue(result["valid"])
        self.assertEqual(result["file_info"]["extension"], "png")

    def test_validate_bonafide_file_none_optional(self):
        """Test file upload is optional - None returns valid."""
        result = validate_bonafide_file(None)
        self.assertTrue(result["valid"])
        self.assertIsNone(result["file_info"])

    def test_validate_bonafide_file_invalid_extension(self):
        """Test validation fails with invalid extension."""
        file = SimpleUploadedFile(
            "bonafide.exe",
            b"content",
            content_type="application/octet-stream"
        )
        with self.assertRaises(FileValidationError):
            validate_bonafide_file(file)

    def test_validate_bonafide_file_exceeds_size(self):
        """Test validation fails when file exceeds size limit."""
        file = SimpleUploadedFile(
            "bonafide.pdf",
            b"x" * (6 * 1024 * 1024),  # 6 MB
            content_type="application/pdf"
        )
        with self.assertRaises(FileValidationError):
            validate_bonafide_file(file)

    def test_validate_bonafide_file_mismatched_content(self):
        """Test validation fails when content doesn't match extension."""
        file = SimpleUploadedFile(
            "bonafide.pdf",
            b"Not a real PDF file",
            content_type="application/pdf"
        )
        with self.assertRaises(FileValidationError) as context:
            validate_bonafide_file(file)
        self.assertIn("does not match", str(context.exception))

    def test_validate_bonafide_file_returns_size_info(self):
        """Test validation returns file size info."""
        jpeg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01" + (b"x" * 1024)
        file = SimpleUploadedFile(
            "bonafide.jpg",
            jpeg_content,
            content_type="image/jpeg"
        )
        result = validate_bonafide_file(file)
        self.assertGreater(result["file_info"]["size"], 0)
        self.assertGreater(result["file_info"]["size_mb"], 0)
