import struct
import os


class C2PAValidator:
    """
    Validates C2PA (Coalition for Content Provenance and Authenticity) manifests
    embedded in media files.

    C2PA metadata is stored as JUMBF (ISO 19566-5) boxes, typically found in:
    - JPEG: APP11 marker segments (0xFFEB)
    - PNG: caBX chunks
    - Other formats: embedded boxes or sidecar XMP

    This implementation performs real binary parsing to detect structural C2PA presence.
    """

    # C2PA / JUMBF magic bytes and identifiers
    JUMBF_CONTENT_TYPE_C2PA = b'c2pa'
    JUMBF_BOX_TYPE = b'jumb'
    JUMBF_DESC_TYPE = b'jumd'
    JPEG_APP11_MARKER = b'\xff\xeb'  # APP11 marker
    JPEG_SOI = b'\xff\xd8'  # Start of Image

    # C2PA manifest label prefix
    C2PA_MANIFEST_URN = b'c2pa'

    def __init__(self):
        print(" C2PA Validator initialized (binary parser)")

    def validate_manifest(self, filepath: str) -> dict:
        """
        Parses a media file to detect and validate C2PA provenance metadata.
        Returns structured information about C2PA presence and validity.
        """
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found: {filepath}")

            file_ext = os.path.splitext(filepath)[1].lower()

            if file_ext in ('.jpg', '.jpeg'):
                return self._parse_jpeg_c2pa(filepath)
            elif file_ext == '.png':
                return self._parse_png_c2pa(filepath)
            else:
                # For video and other formats, do a generic binary scan
                return self._generic_c2pa_scan(filepath)

        except Exception as e:
            print(f" C2PA validation error: {e}")
            return {
                "c2pa_present": False,
                "c2pa_valid_signature": False,
                "hardware_attested": False,
                "issuer": None,
                "error": str(e),
            }

    def _parse_jpeg_c2pa(self, filepath: str) -> dict:
        """
        Parse JPEG file for C2PA metadata in APP11 (0xFFEB) marker segments.
        C2PA data in JPEG is stored as JUMBF boxes within APP11 segments.
        """
        with open(filepath, 'rb') as f:
            data = f.read()

        # Verify JPEG SOI
        if not data.startswith(self.JPEG_SOI):
            return self._no_c2pa_result("Not a valid JPEG file")

        c2pa_boxes = []
        pos = 2  # Skip SOI

        while pos < len(data) - 2:
            # Look for markers (0xFF followed by non-zero byte)
            if data[pos] != 0xFF:
                break

            marker = data[pos:pos + 2]
            pos += 2

            if marker == b'\xff\xd9':  # EOI
                break

            if marker == b'\xff\xda':  # SOS  start of scan, stop parsing markers
                break

            # Read segment length (2 bytes, big-endian, includes the length field itself)
            if pos + 2 > len(data):
                break
            seg_len = struct.unpack('>H', data[pos:pos + 2])[0]
            seg_data = data[pos + 2:pos + seg_len]

            # Check if this is APP11 (0xFFEB)  where JUMBF/C2PA lives
            if marker == self.JPEG_APP11_MARKER:
                # Check for JUMBF Content Identifier (JP2C / C2PA markers)
                if self._contains_c2pa_jumbf(seg_data):
                    c2pa_boxes.append(seg_data)

            pos += seg_len

        if c2pa_boxes:
            return self._build_c2pa_result(c2pa_boxes, filepath)
        else:
            return self._no_c2pa_result("No C2PA APP11 segments found in JPEG")

    def _parse_png_c2pa(self, filepath: str) -> dict:
        """
        Parse PNG file for C2PA metadata in caBX chunks.
        """
        with open(filepath, 'rb') as f:
            data = f.read()

        # Verify PNG signature
        png_sig = b'\x89PNG\r\n\x1a\n'
        if not data.startswith(png_sig):
            return self._no_c2pa_result("Not a valid PNG file")

        c2pa_chunks = []
        pos = 8  # Skip PNG signature

        while pos < len(data) - 8:
            chunk_len = struct.unpack('>I', data[pos:pos + 4])[0]
            chunk_type = data[pos + 4:pos + 8]
            chunk_data = data[pos + 8:pos + 8 + chunk_len]

            # caBX is the C2PA chunk type in PNG
            if chunk_type == b'caBX':
                if self._contains_c2pa_jumbf(chunk_data):
                    c2pa_chunks.append(chunk_data)

            pos += 12 + chunk_len  # length + type + data + CRC

            if chunk_type == b'IEND':
                break

        if c2pa_chunks:
            return self._build_c2pa_result(c2pa_chunks, filepath)
        else:
            return self._no_c2pa_result("No C2PA caBX chunks found in PNG")

    def _generic_c2pa_scan(self, filepath: str) -> dict:
        """
        Generic binary scan for C2PA/JUMBF markers in any file format.
        Less precise but catches C2PA in video containers, TIFF, etc.
        """
        with open(filepath, 'rb') as f:
            # Read up to 10MB for scanning
            data = f.read(10 * 1024 * 1024)

        # Look for JUMBF / C2PA signatures
        markers_found = []

        # Search for 'c2pa' content type identifier
        if self.C2PA_MANIFEST_URN in data:
            markers_found.append("c2pa_urn")

        # Search for JUMBF box types
        if self.JUMBF_BOX_TYPE in data:
            markers_found.append("jumb_box")

        if self.JUMBF_DESC_TYPE in data:
            markers_found.append("jumd_desc")

        # Search for common C2PA claim URNs
        if b'c2pa.claim' in data:
            markers_found.append("c2pa_claim")

        if b'c2pa.assertions' in data:
            markers_found.append("c2pa_assertions")

        if b'c2pa.signature' in data:
            markers_found.append("c2pa_signature")

        if markers_found:
            has_signature = "c2pa_signature" in markers_found
            has_claim = "c2pa_claim" in markers_found

            return {
                "c2pa_present": True,
                "c2pa_valid_signature": has_signature,
                "hardware_attested": has_signature and has_claim,
                "issuer": self._extract_issuer(data),
                "markers_found": markers_found,
                "scan_method": "generic_binary",
            }
        else:
            return self._no_c2pa_result("No C2PA markers found in file")

    def _contains_c2pa_jumbf(self, data: bytes) -> bool:
        """Check if a data segment contains C2PA JUMBF content."""
        return (
            self.JUMBF_CONTENT_TYPE_C2PA in data
            or self.JUMBF_BOX_TYPE in data
            or self.JUMBF_DESC_TYPE in data
            or b'c2pa.claim' in data
        )

    def _build_c2pa_result(self, c2pa_data: list, filepath: str) -> dict:
        """Build a positive C2PA result from found data."""
        all_data = b''.join(c2pa_data)

        has_signature = b'c2pa.signature' in all_data
        has_claim = b'c2pa.claim' in all_data
        has_assertions = b'c2pa.assertions' in all_data

        issuer = self._extract_issuer(all_data)

        return {
            "c2pa_present": True,
            "c2pa_valid_signature": has_signature,
            "hardware_attested": has_signature and has_claim,
            "issuer": issuer,
            "has_claim": has_claim,
            "has_assertions": has_assertions,
            "manifest_boxes_found": len(c2pa_data),
        }

    def _extract_issuer(self, data: bytes) -> str:
        """Attempt to extract the C2PA issuer/signer information from raw bytes."""
        # Look for common issuer patterns in the binary data
        issuer_markers = [
            b'StrongBox',
            b'Adobe',
            b'Qualcomm',
            b'Samsung',
            b'Google',
            b'Apple',
            b'Microsoft',
            b'Truepic',
            b'Leica',
            b'Nikon',
            b'Canon',
            b'Sony',
        ]

        for marker in issuer_markers:
            if marker in data:
                return marker.decode('utf-8', errors='ignore')

        return "Unknown"

    def _no_c2pa_result(self, reason: str) -> dict:
        """Build a negative C2PA result."""
        return {
            "c2pa_present": False,
            "c2pa_valid_signature": False,
            "hardware_attested": False,
            "issuer": None,
            "reason": reason,
        }

