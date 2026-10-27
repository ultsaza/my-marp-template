"""Artifact verifier tests use explicit small fixtures, never catalog evidence."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "verify-science-tokyo-artifacts.py"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"


def pptx_fixture(path, *, width=1280, broken=None):
    """Two explicit full-frame image slides plus a layout (not catalog data)."""
    slides = "".join(f'<p:sldId id="{255 + i}" r:id="rId{i}"/>' for i in (1, 2))
    relationships = "".join(
        f'<Relationship Id="rId{i}" Type="{R}/slide" Target="slides/slide{i}.xml"/>'
        for i in (1, 2)
    )
    with zipfile.ZipFile(path, "w") as archive:
        content_types = '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
        content_types += "".join(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' for i in (1, 2))
        archive.writestr("[Content_Types].xml", content_types + '</Types>')
        archive.writestr("_rels/.rels", f'<Relationships xmlns="{PKG}"><Relationship Id="rId1" Type="{R}/officeDocument" Target="ppt/presentation.xml"/></Relationships>')
        archive.writestr("ppt/presentation.xml", f'<p:presentation xmlns:p="{P}" xmlns:r="{R}"><p:sldIdLst>{slides}</p:sldIdLst><p:sldSz cx="12192000" cy="6858000"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>')
        archive.writestr("ppt/_rels/presentation.xml.rels", f'<Relationships xmlns="{PKG}">{relationships}</Relationships>')
        archive.writestr("ppt/slideLayouts/slideLayout1.xml", f'<p:sldLayout xmlns:p="{P}"/>')
        for i in (1, 2):
            image = io.BytesIO()
            Image.new("RGB", (width, 720), "white" if i == 1 else "black").save(image, format="PNG")
            picture = '<p:pic><p:nvPicPr><p:cNvPr id="2" name="explicit fixture picture"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="rIdImage"/><a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="12192000" cy="6858000"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'
            if broken == "no-picture" and i == 2:
                picture = ""
            archive.writestr(f"ppt/slides/slide{i}.xml", f'<p:sld xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}"><p:cSld><p:spTree>{picture}</p:spTree></p:cSld></p:sld>')
            if broken != "missing-relation" or i != 2:
                extra = ' TargetMode="External"' if broken == "external-image" and i == 2 else ""
                archive.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", f'<Relationships xmlns="{PKG}"><Relationship Id="rIdImage" Type="{R}/image" Target="../media/image{i}.png"{extra}/></Relationships>')
            if broken != "missing-media" or i != 2:
                archive.writestr(f"ppt/media/image{i}.png", image.getvalue())
    return path


def marp_background_fixture(path, *, width=2560, broken=None):
    """Use the background/group XML emitted by Marp, not a p:pic stand-in."""
    pptx_fixture(path)
    with zipfile.ZipFile(path) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    for i in (1, 2):
        image = io.BytesIO()
        Image.new("RGB", (width, 1440), "white" if i == 1 else "black").save(image, format="PNG")
        media = f"ppt/media/Slide-{i}-image-1.png"
        del parts[f"ppt/media/image{i}.png"]
        parts[media] = image.getvalue()
        blip = '<a:blip r:embed="rId1"><a:lum/></a:blip>'
        relation_id, relation_type = "rId1", "image"
        target, extra = f"../media/Slide-{i}-image-1.png", ""
        if i == 2:
            if broken == "missing-identifier":
                relation_id = "rIdMissing"
            elif broken == "linked-image":
                blip = '<a:blip r:link="rId1"><a:lum/></a:blip>'
            elif broken == "external-image":
                extra = ' TargetMode="External"'
            elif broken == "wrong-type":
                relation_type = "slideLayout"
            elif broken == "outside-media":
                target = f"../Slide-{i}-image-1.png"
            elif broken == "missing-media":
                del parts[media]
            elif broken == "invalid-media":
                parts[media] = b"not a PNG image"
        parts[f"ppt/slides/slide{i}.xml"] = f'<p:sld xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}"><p:cSld name="Slide {i}"><p:bg><p:bgPr><a:blipFill dpi="0" rotWithShape="1">{blip}<a:srcRect/><a:stretch><a:fillRect/></a:stretch></a:blipFill><a:effectLst/></p:bgPr></p:bg><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'.encode()
        relations = f"ppt/slides/_rels/slide{i}.xml.rels"
        parts[relations] = f'<Relationships xmlns="{PKG}"><Relationship Id="{relation_id}" Type="{R}/{relation_type}" Target="{target}"{extra}/><Relationship Id="rId2" Type="{R}/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>'.encode()
        if broken == "missing-relation" and i == 2:
            del parts[relations]
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in parts.items():
            archive.writestr(name, data)
    return path


def pdf_geometry_fixture(path, pages):
    """Explicit blank PDF pages: (width points, height points, rotation[, crop])."""
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b""]
    kids = []
    for width, height, rotation, *crop in pages:
        kids.append(f"{len(objects) + 1} 0 R")
        crop_box = f" /CropBox [{' '.join(map(str, crop[0]))}]" if crop else ""
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] /Rotate {rotation}{crop_box} /Resources << >> >>".encode())
    objects[1] = f"<< /Type /Pages /Count {len(kids)} /Kids [{' '.join(kids)}] >>".encode()
    data, offsets = bytearray(b"%PDF-1.4\n"), [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    start = len(data)
    data.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode())
    data.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode())
    path.write_bytes(data)
    return path


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(TOOL.is_file(), "artifact verifier implementation is missing")
        spec = importlib.util.spec_from_file_location("artifact_verifier", TOOL)
        self.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.tool)
        scratch = ROOT / ".verification" / "artifact-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="fixture-", dir=scratch)
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def test_counts_actual_slide_parts_not_slide_layouts(self):
        deck = pptx_fixture(self.directory / "fixture.pptx")
        result = self.tool.inspect_pptx(deck, expected_count=2)
        self.assertEqual(result["slide_count"], 2)
        self.assertEqual([slide["part"] for slide in result["slides"]], ["ppt/slides/slide1.xml", "ppt/slides/slide2.xml"])

    def test_rejects_missing_embedded_relationship_media_or_picture(self):
        for broken in ("missing-relation", "missing-media", "external-image", "no-picture"):
            with self.subTest(broken=broken):
                deck = pptx_fixture(self.directory / f"{broken}.pptx", broken=broken)
                with self.assertRaises(self.tool.VerificationError):
                    self.tool.inspect_pptx(deck, expected_count=2)

    def test_rejects_embedded_picture_narrower_than_1280_pixels(self):
        deck = pptx_fixture(self.directory / "small.pptx", width=1279)
        with self.assertRaisesRegex(self.tool.VerificationError, "1280"):
            self.tool.inspect_pptx(deck, expected_count=2)

    def test_embedded_picture_dimensions_are_measured_from_media(self):
        deck = pptx_fixture(self.directory / "valid.pptx")
        result = self.tool.inspect_pptx(deck, expected_count=2)
        self.assertEqual(result["slides"][1]["pictures"][0]["width"], 1280)
        self.assertEqual(result["slides"][1]["pictures"][0]["height"], 720)

    def test_accepts_full_slide_marp_background_and_measures_embedded_media(self):
        deck = marp_background_fixture(self.directory / "marp-background.pptx")
        result = self.tool.inspect_pptx(deck, expected_count=2)
        self.assertEqual(result["slide_count"], 2)
        for page, slide in enumerate(result["slides"], 1):
            self.assertEqual(slide["pictures"], [{
                "media": f"ppt/media/Slide-{page}-image-1.png", "width": 2560, "height": 1440,
            }])

    def test_marp_background_reuses_strict_relationship_and_media_validation(self):
        failures = {
            "missing-relation": "Missing or invalid XML part",
            "missing-identifier": "Missing embedded picture relationship",
            "linked-image": "Missing embedded picture relationship",
            "external-image": "External or invalid image relationship",
            "wrong-type": "Wrong image relationship type",
            "outside-media": "Picture does not link to package media",
            "missing-media": "Missing or invalid picture media",
            "invalid-media": "Missing or invalid picture media",
        }
        for broken, message in failures.items():
            with self.subTest(broken=broken):
                deck = marp_background_fixture(self.directory / f"marp-{broken}.pptx", broken=broken)
                with self.assertRaisesRegex(self.tool.VerificationError, message):
                    self.tool.inspect_pptx(deck, expected_count=2)

    def test_rejects_marp_background_narrower_than_1280_pixels(self):
        deck = marp_background_fixture(self.directory / "marp-small.pptx", width=1279)
        with self.assertRaisesRegex(self.tool.VerificationError, "at least 1280 pixels wide"):
            self.tool.inspect_pptx(deck, expected_count=2)

    def test_rejects_wrong_actual_slide_count(self):
        deck = pptx_fixture(self.directory / "wrong-count.pptx")
        with self.assertRaisesRegex(self.tool.VerificationError, "expected 65"):
            self.tool.inspect_pptx(deck)

    def test_pixel_difference_reports_normalized_actual_mutation(self):
        self.assertTrue(hasattr(self.tool, "compare_images"), "pixel comparison is missing")
        left = self.directory / "left.png"
        right = self.directory / "right.png"
        Image.new("RGB", (1280, 720), "black").save(left)
        Image.new("RGB", (1280, 720), "black").save(right)
        self.assertEqual(self.tool.compare_images(left, right)["mean_absolute_difference"], 0.0)
        with Image.open(right) as image:
            image.putpixel((0, 0), (255, 0, 0))
            image.save(right)
        result = self.tool.compare_images(left, right)
        self.assertAlmostEqual(result["mean_absolute_difference"], 1 / (1280 * 720 * 3))
        self.assertAlmostEqual(result["different_pixel_fraction"], 1 / (1280 * 720))
        self.assertEqual(result["max_absolute_difference"], 1.0)

    def test_pixel_comparison_rejects_missing_or_wrong_sized_images(self):
        self.assertTrue(hasattr(self.tool, "compare_images"), "pixel comparison is missing")
        valid = self.directory / "valid.png"
        small = self.directory / "small.png"
        Image.new("RGB", (1280, 720), "black").save(valid)
        Image.new("RGB", (640, 360), "black").save(small)
        for invalid in (small, self.directory / "missing.png"):
            with self.subTest(path=invalid), self.assertRaises(self.tool.VerificationError):
                self.tool.compare_images(valid, invalid)

    def test_manifest_preserves_expected_id_order_and_requires_exact_count(self):
        self.assertTrue(hasattr(self.tool, "load_patterns"), "manifest validation is missing")
        manifest = self.directory / "manifest.json"
        patterns = [
            {"key": "b02", "id": "second_named_pattern", "slide": 1},
            {"key": "b01", "id": "first_named_pattern", "slide": 2},
        ]
        manifest.write_text(json.dumps({"patterns": patterns}), encoding="utf-8")
        self.assertEqual(self.tool.load_patterns(manifest, expected_count=2), patterns)
        with self.assertRaisesRegex(self.tool.VerificationError, "65"):
            self.tool.load_patterns(manifest)
        for bad_patterns in ([patterns[0], patterns[0]], [patterns[1], patterns[0]]):
            manifest.write_text(json.dumps({"patterns": bad_patterns}), encoding="utf-8")
            with self.assertRaises(self.tool.VerificationError):
                self.tool.load_patterns(manifest, expected_count=2)

    def test_missing_page_is_rejected_even_if_another_page_is_present(self):
        self.assertTrue(hasattr(self.tool, "require_page_images"), "page inventory is missing")
        pages = self.directory / "html"
        pages.mkdir()
        Image.new("RGB", (1280, 720), "white").save(pages / "page-001.png")
        with self.assertRaisesRegex(self.tool.VerificationError, "page-002.png"):
            self.tool.require_page_images(pages, 2)
        Image.new("RGB", (1280, 720), "white").save(pages / "page-002.png")
        self.assertEqual(len(self.tool.require_page_images(pages, 2)), 2)
        Image.new("RGB", (1280, 720), "white").save(pages / "page-003.png")
        with self.assertRaisesRegex(self.tool.VerificationError, "page-003.png"):
            self.tool.require_page_images(pages, 2)

    @unittest.skipUnless(shutil.which("pdfinfo") and (shutil.which("pdftoppm") or shutil.which("pdftocairo")), "requires installed Poppler")
    def test_renders_every_real_pdf_page_to_exact_size_and_canonical_names(self):
        self.assertTrue(hasattr(self.tool, "render_pdf"), "PDF rendering is missing")
        pdf = self.directory / "two-page-fixture.pdf"
        white = Image.new("RGB", (1280, 720), "white")
        black = Image.new("RGB", (1280, 720), "black")
        white.save(pdf, format="PDF", save_all=True, append_images=[black], resolution=96)
        self.assertEqual(self.tool.count_pdf_pages(pdf), 2)
        destination = self.directory / "rendered"
        destination.mkdir()
        Image.new("RGB", (1280, 720), "red").save(destination / "page-003.png")
        pages = self.tool.render_pdf(pdf, destination, expected_count=2)
        self.assertEqual([page.name for page in pages], ["page-001.png", "page-002.png"])
        self.assertFalse((destination / "page-003.png").exists(), "stale renders must not survive")
        with Image.open(pages[0]) as first, Image.open(pages[1]) as second:
            self.assertEqual(first.size, (1280, 720))
            self.assertEqual(second.size, (1280, 720))
            self.assertEqual(first.getpixel((640, 360))[:3], (255, 255, 255))
            self.assertEqual(second.getpixel((640, 360))[:3], (0, 0, 0))
        with self.assertRaisesRegex(self.tool.VerificationError, "expected 65"):
            self.tool.render_pdf(pdf, destination)

    @unittest.skipUnless(shutil.which("pdfinfo") and (shutil.which("pdftoppm") or shutil.which("pdftocairo")), "requires installed Poppler")
    def test_pdf_geometry_rejects_every_wrong_effective_page_before_rasterizing(self):
        cases = {
            "square": [(720, 720, 0)],
            "second-page-square": [(960, 540, 0), (720, 720, 0)],
            "rotated-to-portrait": [(960, 540, 0), (960, 540, 90)],
            "portrait": [(540, 960, 0)],
            "square-crop": [(960, 540, 0, (0, 0, 540, 540))],
        }
        for name, geometry in cases.items():
            with self.subTest(case=name):
                pdf = pdf_geometry_fixture(self.directory / f"{name}.pdf", geometry)
                output = self.directory / f"{name}-render"
                with mock.patch.object(self.tool, "run_command", wraps=self.tool.run_command) as commands:
                    with self.assertRaisesRegex(self.tool.VerificationError, r"PDF .*page \d+.*16:9"):
                        self.tool.render_pdf(pdf, output, expected_count=len(geometry))
                self.assertFalse(output.exists(), "reject geometry before creating render output")
                self.assertTrue(all(Path(call.args[0][0]).name == "pdfinfo" for call in commands.call_args_list))

    @unittest.skipUnless(shutil.which("pdfinfo") and (shutil.which("pdftoppm") or shutil.which("pdftocairo")), "requires installed Poppler")
    def test_pdf_geometry_accepts_effective_widescreen_rotations(self):
        geometry = [(960, 540, 0), (540, 960, 90), (960, 540, 180), (540, 960, 270)]
        pdf = pdf_geometry_fixture(self.directory / "rotated-widescreen.pdf", geometry)
        frames = self.tool.render_pdf(pdf, self.directory / "rotated-render", expected_count=4)
        self.assertEqual(len(frames), 4)

    def test_pptx_geometry_rejects_wrong_or_missing_slide_size_before_media(self):
        sizes = ('<p:sldSz cx="720" cy="720"/>', '<p:sldSz cx="720" cy="1280"/>', "")
        for index, size in enumerate(sizes):
            with self.subTest(size=size):
                deck = pptx_fixture(self.directory / f"wrong-geometry-{index}.pptx")
                with zipfile.ZipFile(deck) as archive:
                    parts = {name: archive.read(name) for name in archive.namelist()}
                parts["ppt/presentation.xml"] = parts["ppt/presentation.xml"].replace(b'<p:sldSz cx="12192000" cy="6858000"/>', size.encode())
                with zipfile.ZipFile(deck, "w") as archive:
                    for name, data in parts.items():
                        archive.writestr(name, data)
                with mock.patch.object(self.tool, "inspect_pictures", wraps=self.tool.inspect_pictures) as inspect:
                    with self.assertRaisesRegex(self.tool.VerificationError, "PPTX slide geometry.*16:9"):
                        self.tool.inspect_pptx(deck, expected_count=2)
                inspect.assert_not_called()

    def test_subprocess_failure_is_real_and_keeps_exit_code_and_stderr(self):
        self.assertTrue(hasattr(self.tool, "run_command"), "checked subprocess runner is missing")
        with self.assertRaisesRegex(self.tool.VerificationError, "fixture renderer failed") as failure:
            self.tool.run_command([sys.executable, "-c", "import sys; print('fixture renderer failed', file=sys.stderr); sys.exit(7)"])
        self.assertIn("7", str(failure.exception))

    @unittest.skipUnless(shutil.which("soffice") and shutil.which("pdfinfo") and (shutil.which("pdftoppm") or shutil.which("pdftocairo")), "requires installed LibreOffice and Poppler")
    def test_converts_whole_two_slide_pptx_with_real_libreoffice(self):
        self.assertTrue(hasattr(self.tool, "convert_pptx_to_pdf"), "PPTX conversion is missing")
        deck = pptx_fixture(self.directory / "two-slide-fixture.pptx")
        output = self.directory / "converted"
        with mock.patch.object(self.tool.subprocess, "run", wraps=subprocess.run) as command_spy:
            pdf = self.tool.convert_pptx_to_pdf(deck, output)
        command = command_spy.call_args
        self.assertTrue(any(argument.startswith("-env:UserInstallation=" + output.resolve().as_uri() + "/") for argument in command.args[0]))
        self.assertIn("TMPDIR", command.kwargs["env"], "LibreOffice temp files must stay under the verification directory")
        self.assertTrue(Path(command.kwargs["env"]["TMPDIR"]).is_relative_to(output.resolve()))
        self.assertEqual(self.tool.count_pdf_pages(pdf), 2)
        pages = self.tool.render_pdf(pdf, output, expected_count=2)
        with Image.open(pages[0]) as first, Image.open(pages[1]) as second:
            self.assertEqual(first.getpixel((640, 360))[:3], (255, 255, 255))
            self.assertEqual(second.getpixel((640, 360))[:3], (0, 0, 0))
        self.assertFalse(list(output.glob(".soffice-*")), "isolated profiles must be cleaned")

    def test_contact_sheets_include_every_format_and_all_65_patterns(self):
        self.assertTrue(hasattr(self.tool, "make_contact_sheets"), "contact sheets are missing")
        formats = ("html", "pdf", "pptx")
        colors = ((255, 0, 0), (0, 255, 0), (0, 0, 255))
        directories = {}
        for name, color in zip(formats, colors):
            directory = self.directory / name
            directory.mkdir()
            source = directory / "fixture-source.png"
            Image.new("RGB", (1280, 720), color).save(source)
            for page in range(1, 66):
                (directory / f"page-{page:03d}.png").hardlink_to(source)
            directories[name] = directory
        patterns = [{"key": f"f{page:02d}", "id": f"explicit_fixture_{page:02d}", "slide": page} for page in range(1, 66)]
        output = self.directory / "contacts"
        output.mkdir()
        Image.new("RGB", (1, 1)).save(output / "contact-18.png")
        sheets = self.tool.make_contact_sheets(patterns, directories, output)
        self.assertEqual(len(sheets), 17)
        self.assertEqual(len(list(output.glob("contact-*.png"))), 17)
        captions = []
        for sheet in sheets:
            with Image.open(sheet) as image:
                self.assertEqual(image.size, (3 * 400, 4 * (225 + 36)))
                captions.extend(image.info["captions"].splitlines())
        for pattern in patterns:
            for name in formats:
                self.assertIn(f'{pattern["key"]} {pattern["id"]} | {name.upper()}', captions)
        self.assertEqual(len(captions), 65 * 3)
        with Image.open(sheets[0]) as image:
            for column, color in enumerate(colors):
                self.assertEqual(image.getpixel((column * 400 + 200, 100)), color)

    def catalog_fixture(self):
        """Small declared fixture only; not evidence for the real 65-slide deck."""
        manifest = self.directory / "fixture-manifest.json"
        patterns = [{"key": "f01", "id": "white_fixture", "slide": 1}, {"key": "f02", "id": "black_fixture", "slide": 2}]
        manifest.write_text(json.dumps({"patterns": patterns}), encoding="utf-8")
        html = self.directory / "html"
        html.mkdir()
        white = Image.new("RGB", (1280, 720), "white")
        black = Image.new("RGB", (1280, 720), "black")
        white.save(html / "page-001.png")
        black.save(html / "page-002.png")
        pdf = self.directory / "fixture.pdf"
        white.save(pdf, format="PDF", save_all=True, append_images=[black], resolution=96)
        deck = pptx_fixture(self.directory / "fixture.pptx")
        inputs = dict(pdf=pdf, pptx=deck, manifest=manifest, output=self.directory / "output", html_dir=html)
        self.bind_layout_receipt(inputs)
        return inputs

    def bind_layout_receipt(self, inputs):
        """Declared synthetic receipt for this white/black unit fixture only."""
        source = self.directory / "fixture-source.html"
        if not source.exists():
            source.write_text("<html><section>EXPLICIT WHITE FIXTURE</section><section>EXPLICIT BLACK FIXTURE</section></html>")
        def binding(path):
            return {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        receipt = {
            "schema_version": 2, "passed": True, "errors": [], "html": str(source.resolve()),
            "expected": 2, "checked": 2, "issues": 0, "slides": [{"number": page, "issues": []} for page in (1, 2)],
            "inputs": {"html": binding(source), "catalog": binding(inputs["manifest"])},
            "screenshots": [dict(binding(inputs["html_dir"] / f"page-{page:03d}.png"), page=page) for page in (1, 2)],
        }
        path = inputs.get("layout_report", inputs["output"] / "layout-report.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt), encoding="utf-8")
        return path

    @unittest.skipUnless(shutil.which("soffice") and shutil.which("pdfinfo") and (shutil.which("pdftoppm") or shutil.which("pdftocairo")), "requires installed LibreOffice and Poppler")
    def test_orchestration_records_real_hashes_counts_and_every_page_metric(self):
        self.assertTrue(hasattr(self.tool, "verify_artifacts"), "artifact orchestration is missing")
        inputs = self.catalog_fixture()
        report = self.tool.verify_artifacts(**inputs, expected_count=2)
        self.assertTrue(report["passed"], report["errors"])
        self.assertEqual(report, json.loads((inputs["output"] / "artifact-report.json").read_text()))
        self.assertEqual(report["counts"], {"manifest": 2, "html": 2, "pdf": 2, "pptx": 2, "pptx_pdf": 2})
        self.assertEqual([page["id"] for page in report["pages"]], ["white_fixture", "black_fixture"])
        for name in ("pdf", "pptx", "manifest"):
            self.assertEqual(report["inputs"][name]["sha256"], hashlib.sha256(inputs[name].read_bytes()).hexdigest())
        self.assertEqual(len(report["inputs"]["html"]), 2)
        for page in report["pages"]:
            self.assertEqual(page["html_pdf"]["mean_absolute_difference"], 0.0)
            self.assertEqual(page["pdf_pptx"]["mean_absolute_difference"], 0.0)
        self.assertEqual(len(report["contact_sheets"]), 1)
        self.assertTrue(report["inputs"]["pptx_pdf"]["sha256"])

    @unittest.skipUnless(shutil.which("soffice") and shutil.which("pdfinfo") and (shutil.which("pdftoppm") or shutil.which("pdftocairo")), "requires installed LibreOffice and Poppler")
    def test_visual_mismatch_fails_without_skipping_remaining_metrics_or_contacts(self):
        self.assertTrue(hasattr(self.tool, "verify_artifacts"), "artifact orchestration is missing")
        inputs = self.catalog_fixture()
        Image.new("RGB", (1280, 720), "black").save(inputs["html_dir"] / "page-001.png")
        self.bind_layout_receipt(inputs)
        report = self.tool.verify_artifacts(**inputs, expected_count=2)
        self.assertFalse(report["passed"])
        self.assertEqual(report["tolerance"], 0.04)
        self.assertEqual(report["pages"][0]["html_pdf"]["mean_absolute_difference"], 1.0)
        self.assertFalse(report["pages"][0]["html_pdf"]["passed"])
        self.assertTrue(report["pages"][1]["passed"])
        self.assertEqual(len(report["contact_sheets"]), 1)
        self.assertTrue(report["errors"])

    def test_layout_receipt_missing_fails_despite_existing_valid_pngs(self):
        inputs = self.catalog_fixture()
        (inputs["output"] / "layout-report.json").unlink()
        report = self.tool.verify_artifacts(**inputs, expected_count=2)
        self.assertFalse(report["passed"])
        self.assertTrue(any("layout receipt" in error.lower() for error in report["errors"]))
        self.assertIsNone(report["max_mean_absolute_differences"])
        self.assertEqual(report["contact_sheets"], [])
        self.assertEqual(json.loads((inputs["output"] / "artifact-report.json").read_text()), report)

    def test_layout_receipt_cli_never_accepts_existing_pngs_without_a_receipt(self):
        inputs = self.catalog_fixture()
        # Explicit inventory-only fixture: no real 65-page exports are claimed.
        inputs["manifest"].write_text(json.dumps({"patterns": [
            {"key": f"f{page:02d}", "id": f"explicit_fixture_{page}", "slide": page} for page in range(1, 66)
        ]}))
        for page in range(3, 66):
            (inputs["html_dir"] / f"page-{page:03d}.png").hardlink_to(inputs["html_dir"] / "page-001.png")
        (inputs["output"] / "layout-report.json").unlink()
        command = [sys.executable, str(TOOL)]
        for name in ("pdf", "pptx", "manifest", "output", "html_dir"):
            command += ["--" + name.replace("_", "-"), str(inputs[name])]
        for extra in ([], ["--layout-report", str(self.directory / "missing-custom-receipt.json")]):
            with self.subTest(arguments=extra):
                result = subprocess.run(command + extra, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                report = json.loads((inputs["output"] / "artifact-report.json").read_text())
                self.assertFalse(report["passed"])
                self.assertTrue(any("layout receipt" in error.lower() for error in report["errors"]), report["errors"])
                self.assertIsNone(report["max_mean_absolute_differences"])

    def test_layout_receipt_rejects_failed_status_and_invalid_bindings(self):
        inputs = self.catalog_fixture()
        path = inputs["output"] / "layout-report.json"
        original = json.loads(path.read_text())
        mutations = {
            "old-schema": lambda r: r.update(schema_version=1),
            "failed": lambda r: r.update(passed=False),
            "nonboolean-pass": lambda r: r.update(passed=1),
            "issues": lambda r: r.update(issues=1),
            "errors": lambda r: r.update(errors=["audit failed"]),
            "expected-count": lambda r: r.update(expected=3),
            "checked-count": lambda r: r.update(checked=1),
            "no-catalog": lambda r: r["inputs"].update(catalog=None),
            "wrong-catalog-path": lambda r: r["inputs"]["catalog"].update(path=str(self.directory / "other-manifest.json")),
            "relative-html-path": lambda r: r["inputs"]["html"].update(path="fixture-source.html"),
            "missing-html-hash": lambda r: r["inputs"]["html"].update(sha256=None),
            "wrong-html-source": lambda r: r.update(html=str(self.directory / "other.html")),
            "missing-screenshot": lambda r: r["screenshots"].pop(),
            "duplicate-page": lambda r: r["screenshots"][1].update(page=1),
            "wrong-screenshot-path": lambda r: r["screenshots"][1].update(path=r["screenshots"][0]["path"]),
            "wrong-screenshot-hash": lambda r: r["screenshots"][1].update(sha256="0" * 64),
        }
        for case, mutate in mutations.items():
            with self.subTest(case=case):
                receipt = json.loads(json.dumps(original))
                mutate(receipt)
                path.write_text(json.dumps(receipt))
                with mock.patch.object(self.tool, "verify_exports") as exports:
                    report = self.tool.verify_artifacts(**inputs, expected_count=2)
                self.assertFalse(report["passed"])
                self.assertTrue(any("layout receipt" in error.lower() for error in report["errors"]), report["errors"])
                exports.assert_not_called()

    def test_layout_receipt_hashes_bind_current_html_catalog_and_each_png(self):
        inputs = self.catalog_fixture()
        sources = [self.directory / "fixture-source.html", inputs["manifest"], inputs["html_dir"] / "page-002.png"]
        originals = {path: path.read_bytes() for path in sources}
        for source in sources:
            with self.subTest(source=source.name):
                for path, data in originals.items():
                    path.write_bytes(data)
                if source.suffix == ".png":
                    with Image.open(source) as image:
                        image.putpixel((0, 0), (127, 0, 0))
                        image.save(source)
                else:
                    source.write_bytes(source.read_bytes() + b"\n ")
                report = self.tool.verify_artifacts(**inputs, expected_count=2)
                self.assertFalse(report["passed"])
                self.assertTrue(any("layout receipt" in error.lower() and "hash" in error.lower() for error in report["errors"]), report["errors"])
                self.assertIsNone(report["max_mean_absolute_differences"])

    def test_layout_receipt_and_html_source_are_protected_from_render_aliases(self):
        inputs = self.catalog_fixture()
        sources = [inputs["output"] / "layout-report.json", self.directory / "fixture-source.html"]
        frame = inputs["output"] / "pdf" / "page-001.png"
        frame.parent.mkdir()
        contact = inputs["output"] / "contact-01.png"
        for source in sources:
            with self.subTest(source=source.name):
                frame.unlink(missing_ok=True)
                frame.symlink_to(source)
                contact.write_bytes(b"must not remove on alias rejection")
                before = source.read_bytes()
                report = self.tool.verify_artifacts(**inputs, expected_count=2)
                self.assertFalse(report["passed"])
                self.assertTrue(any("overlap" in error.lower() for error in report["errors"]), report["errors"])
                self.assertTrue(frame.is_symlink())
                self.assertEqual(source.read_bytes(), before)
                self.assertEqual(contact.read_bytes(), b"must not remove on alias rejection")

    @unittest.skipUnless(shutil.which("soffice") and shutil.which("pdfinfo") and (shutil.which("pdftoppm") or shutil.which("pdftocairo")), "requires installed LibreOffice and Poppler")
    def test_layout_receipt_explicit_path_is_supported_and_recorded(self):
        inputs = self.catalog_fixture()
        custom = self.directory / "custom-layout-report.json"
        (inputs["output"] / "layout-report.json").replace(custom)
        inputs["layout_report"] = custom
        report = self.tool.verify_artifacts(**inputs, expected_count=2)
        self.assertTrue(report["passed"], report["errors"])
        self.assertEqual(report["inputs"]["layout_report"]["sha256"], hashlib.sha256(custom.read_bytes()).hexdigest())
        self.assertEqual(report["inputs"]["html_source"]["sha256"], hashlib.sha256((self.directory / "fixture-source.html").read_bytes()).hexdigest())

    def test_missing_page_failure_is_written_without_inventing_pixel_metrics(self):
        self.assertTrue(hasattr(self.tool, "verify_artifacts"), "artifact orchestration is missing")
        inputs = self.catalog_fixture()
        (inputs["html_dir"] / "page-002.png").unlink()
        report = self.tool.verify_artifacts(**inputs, expected_count=2)
        self.assertFalse(report["passed"])
        self.assertTrue(any("page-002.png" in error for error in report["errors"]))
        self.assertEqual(len(report["pages"]), 2)
        self.assertIsNone(report["pages"][1]["html_pdf"])
        self.assertIsNone(report["pages"][1]["pdf_pptx"])
        self.assertTrue((inputs["output"] / "artifact-report.json").is_file())

    def test_cli_missing_inputs_exits_nonzero_with_report(self):
        output = self.directory / "cli-output"
        command = [sys.executable, str(TOOL), "--pdf", str(self.directory / "missing.pdf"), "--pptx", str(self.directory / "missing.pptx"), "--manifest", str(self.directory / "missing.json"), "--output", str(output)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = json.loads((output / "artifact-report.json").read_text())
        self.assertFalse(report["passed"])
        self.assertIsNone(report["inputs"]["pdf"]["sha256"])
        help_result = subprocess.run([sys.executable, str(TOOL), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("pdf/science-tokyo-catalog.pdf", help_result.stdout)
        self.assertIn("--layout-report", help_result.stdout)
        for tolerance in ("nan", "0.05", "-0.01"):
            invalid = subprocess.run([sys.executable, str(TOOL), "--tolerance", tolerance], capture_output=True, text=True)
            self.assertEqual(invalid.returncode, 2, invalid.stdout + invalid.stderr)

    def test_failed_prerequisite_removes_stale_owned_evidence_not_html_inputs(self):
        self.assertTrue(hasattr(self.tool, "verify_artifacts"), "artifact orchestration is missing")
        inputs = self.catalog_fixture()
        (inputs["html_dir"] / "page-002.png").unlink()
        stale = []
        for name in ("pdf", "pptx"):
            directory = inputs["output"] / name
            directory.mkdir(parents=True)
            frame = directory / "page-001.png"
            Image.new("RGB", (1280, 720), "red").save(frame)
            stale.append(frame)
        contact = inputs["output"] / "contact-01.png"
        Image.new("RGB", (1, 1)).save(contact)
        stale.append(contact)
        original_hash = hashlib.sha256((inputs["html_dir"] / "page-001.png").read_bytes()).hexdigest()
        report = self.tool.verify_artifacts(**inputs, expected_count=2)
        self.assertFalse(report["passed"])
        self.assertFalse(any(path.exists() for path in stale), "stale renders/contacts must not look like current evidence")
        self.assertEqual(hashlib.sha256((inputs["html_dir"] / "page-001.png").read_bytes()).hexdigest(), original_hash)

    def test_report_destination_rejects_manifest_alias_before_any_mutation(self):
        inputs = self.catalog_fixture()
        inputs["output"].mkdir(exist_ok=True)
        destination = inputs["output"] / "artifact-report.json"
        inputs["manifest"].replace(destination)
        inputs["manifest"] = destination
        stale = inputs["output"] / "contact-01.png"
        stale.write_bytes(b"untouched stale evidence")
        before = {path: path.read_bytes() for path in (inputs["pdf"], inputs["pptx"], destination, stale)}
        with self.assertRaisesRegex(self.tool.VerificationError, "report destination.*input"):
            self.tool.verify_artifacts(**inputs, expected_count=2)
        self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_report_destination_rejects_symlink_aliases_to_all_inputs(self):
        inputs = self.catalog_fixture()
        inputs["output"].mkdir(exist_ok=True)
        destination = inputs["output"] / "artifact-report.json"
        sources = [inputs[name] for name in ("pdf", "pptx", "manifest")]
        sources += sorted(inputs["html_dir"].glob("page-*.png"))
        sources += [inputs["output"] / "layout-report.json", self.directory / "fixture-source.html"]
        for source in sources:
            with self.subTest(source=source.name):
                before = {path: path.read_bytes() for path in sources}
                destination.symlink_to(source)
                try:
                    with self.assertRaisesRegex(self.tool.VerificationError, "report destination.*input"):
                        self.tool.verify_artifacts(**inputs, expected_count=2)
                    self.assertEqual({path: path.read_bytes() for path in before}, before)
                    self.assertTrue(destination.is_symlink())
                finally:
                    destination.unlink(missing_ok=True)

    def test_report_destination_rejects_hardlink_aliases_to_all_inputs(self):
        inputs = self.catalog_fixture()
        destination = inputs["output"] / "artifact-report.json"
        sources = [inputs[name] for name in ("pdf", "pptx", "manifest")]
        sources += sorted(inputs["html_dir"].glob("page-*.png"))
        sources += [inputs["output"] / "layout-report.json", self.directory / "fixture-source.html"]
        stale = inputs["output"] / "contact-01.png"
        stale.write_bytes(b"untouched stale evidence")
        for source in sources:
            with self.subTest(source=source.name):
                before = {path: path.read_bytes() for path in sources + [stale]}
                destination.hardlink_to(source)
                try:
                    with self.assertRaisesRegex(self.tool.VerificationError, "report destination.*input"):
                        self.tool.reject_report_alias(inputs["output"], sources)
                    self.assertEqual({path: path.read_bytes() for path in before}, before)
                    self.assertTrue(destination.samefile(source))
                finally:
                    destination.unlink(missing_ok=True)

    def test_rejects_html_input_aliasing_render_output_without_deleting_it(self):
        self.assertTrue(hasattr(self.tool, "verify_artifacts"), "artifact orchestration is missing")
        inputs = self.catalog_fixture()
        inputs["output"].mkdir(exist_ok=True)
        (inputs["output"] / "pdf").symlink_to(inputs["html_dir"], target_is_directory=True)
        before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs["html_dir"].glob("page-*.png")}
        report = self.tool.verify_artifacts(**inputs, expected_count=2)
        self.assertFalse(report["passed"])
        self.assertTrue(any("overlap" in error.lower() for error in report["errors"]))
        self.assertEqual({path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs["html_dir"].glob("page-*.png")}, before)


if __name__ == "__main__":
    unittest.main()
