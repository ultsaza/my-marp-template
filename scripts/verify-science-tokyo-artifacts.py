#!/usr/bin/env python3
"""Verify Science Tokyo export structure and rendered visual equivalence."""
import argparse
import hashlib
import io
import math
import json
import os
from pathlib import Path
import posixpath
import re
import shutil
import subprocess
import tempfile
import textwrap
import zipfile
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlsplit

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat
from PIL.PngImagePlugin import PngInfo

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
CANVAS = (1280, 720)


class VerificationError(RuntimeError):
    """An actual input, renderer, or comparison failed verification."""


def read_xml(archive, part):
    try:
        return ET.fromstring(archive.read(part))
    except (KeyError, ET.ParseError) as error:
        raise VerificationError(f"Missing or invalid XML part {part}: {error}") from error


def relationships(archive, source):
    parent, name = posixpath.split(source)
    root = read_xml(archive, posixpath.join(parent, "_rels", name + ".rels"))
    result = {}
    for relation in root.findall(f"{{{PKG}}}Relationship"):
        identifier = relation.get("Id")
        if not identifier or identifier in result:
            raise VerificationError(f"Missing/duplicate relationship ID in {source}")
        result[identifier] = relation.attrib
    return result


def resolve_part(source, relation, kind):
    target = relation.get("Target", "")
    url = urlsplit(target)
    if (relation.get("TargetMode", "Internal") != "Internal" or url.scheme or url.netloc
            or url.query or url.fragment or "\\\\" in target or not target):
        raise VerificationError(f"External or invalid {kind} relationship in {source}: {target}")
    if relation.get("Type") != f"{R}/{kind}":
        raise VerificationError(f"Wrong {kind} relationship type in {source}")
    path = unquote(url.path)
    resolved = posixpath.normpath(path.lstrip("/") if path.startswith("/") else posixpath.join(posixpath.dirname(source), path))
    if resolved.startswith("../") or not resolved.startswith("ppt/"):
        raise VerificationError(f"Relationship escapes PPTX package: {target}")
    return resolved


def inspect_pictures(archive, part):
    root = read_xml(archive, part)
    if root.tag != f"{{{P}}}sld":
        raise VerificationError(f"Not a real slide XML part: {part}")
    pictures = root.findall(f".//{{{P}}}pic")
    # Marp stores its full-slide image in the background rather than a p:pic.
    pictures += root.findall(f"{{{P}}}cSld/{{{P}}}bg/{{{P}}}bgPr/{{{A}}}blipFill")
    if not pictures:
        raise VerificationError(f"No embedded picture on {part}")
    relations = relationships(archive, part)
    result = []
    for picture in pictures:
        blip = picture.find(f".//{{{A}}}blip")
        identifier = blip.get(f"{{{R}}}embed") if blip is not None else None
        if identifier not in relations:
            raise VerificationError(f"Missing embedded picture relationship on {part}: {identifier}")
        media = resolve_part(part, relations[identifier], "image")
        if not media.startswith("ppt/media/"):
            raise VerificationError(f"Picture does not link to package media: {media}")
        try:
            with Image.open(io.BytesIO(archive.read(media))) as image:
                width, height = image.size
                image.verify()
        except (KeyError, OSError, ValueError) as error:
            raise VerificationError(f"Missing or invalid picture media {media}: {error}") from error
        result.append({"media": media, "width": width, "height": height})
    if not any(picture["width"] >= CANVAS[0] for picture in result):
        raise VerificationError(f"Slide {part} needs an embedded picture at least {CANVAS[0]} pixels wide")
    return result


def inspect_pptx(path, expected_count=65):
    """Count actual slide parts and inspect pictures in presentation order."""
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise VerificationError("Duplicate ZIP part names in PPTX")
            parts = {name for name in names if re.fullmatch(r"ppt/slides/slide[1-9]\d*\.xml", name)}
            if len(parts) != expected_count:
                raise VerificationError(f"PPTX has {len(parts)} slide parts; expected {expected_count}")
            source = "ppt/presentation.xml"
            root = read_xml(archive, source)
            size = root.find(f"{{{P}}}sldSz")
            try:
                width, height = (int(size.get(name, "")) for name in ("cx", "cy"))
            except (AttributeError, ValueError) as error:
                raise VerificationError("PPTX slide geometry must specify widescreen 16:9 dimensions") from error
            if width <= 0 or height <= 0 or width * CANVAS[1] != height * CANVAS[0]:
                raise VerificationError(f"PPTX slide geometry {width} x {height} must be widescreen 16:9")
            relations = relationships(archive, source)
            ordered = []
            for slide in root.findall(f"{{{P}}}sldIdLst/{{{P}}}sldId"):
                identifier = slide.get(f"{{{R}}}id")
                if identifier not in relations:
                    raise VerificationError(f"Missing slide relationship: {identifier}")
                ordered.append(resolve_part(source, relations[identifier], "slide"))
            if len(ordered) != expected_count or set(ordered) != parts:
                raise VerificationError("Presentation slide order/count does not match actual slide parts")
            return {"slide_count": len(parts), "slides": [
                {"page": page, "part": part, "pictures": inspect_pictures(archive, part)}
                for page, part in enumerate(ordered, 1)
            ]}
    except (OSError, zipfile.BadZipFile) as error:
        raise VerificationError(f"Cannot inspect PPTX {path}: {error}") from error


def load_image(path):
    """Load an exact-size frame; never resize away a mismatch."""
    try:
        with Image.open(path) as image:
            if image.size != CANVAS:
                raise VerificationError(f"Image {path} is {image.size}; expected {CANVAS}")
            rgba = image.convert("RGBA")
            background = Image.new("RGBA", CANVAS, "white")
            return Image.alpha_composite(background, rgba).convert("RGB")
    except (OSError, ValueError) as error:
        raise VerificationError(f"Cannot read image {path}: {error}") from error


def load_patterns(path, expected_count=65):
    """Read the manifest as the sole source of pattern identity/order."""
    try:
        manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise VerificationError(f"Cannot read manifest {path}: {error}") from error
    patterns = manifest.get("patterns") if isinstance(manifest, dict) else None
    if not isinstance(patterns, list) or len(patterns) != expected_count:
        raise VerificationError(f"Manifest must contain exactly {expected_count} patterns")
    keys, identifiers = set(), set()
    for page, pattern in enumerate(patterns, 1):
        if not isinstance(pattern, dict) or pattern.get("slide") != page:
            raise VerificationError(f"Manifest slide order is invalid at page {page}")
        key, identifier = pattern.get("key"), pattern.get("id")
        if not all(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]+", value) for value in (key, identifier)):
            raise VerificationError(f"Manifest key/ID must be nonempty ASCII identifiers at page {page}")
        if key in keys or identifier in identifiers:
            raise VerificationError(f"Duplicate manifest key/ID at page {page}")
        keys.add(key)
        identifiers.add(identifier)
    return patterns


def require_page_images(directory, expected_count):
    directory = Path(directory)
    expected = [directory / f"page-{page:03d}.png" for page in range(1, expected_count + 1)]
    missing = set(expected) - set(directory.glob("page-*.png"))
    extra = set(directory.glob("page-*.png")) - set(expected)
    if missing or extra:
        raise VerificationError(f"Page inventory mismatch in {directory}; missing={[path.name for path in sorted(missing)]}; extra={[path.name for path in sorted(extra)]}")
    for path in expected:
        load_image(path).close()
    return expected


def run_command(arguments, timeout=600, cwd=None, env=None):
    """Run an explicit argv without a shell; surface failures verbatim."""
    try:
        return subprocess.run(
            [str(argument) for argument in arguments], check=True, capture_output=True,
            text=True, timeout=timeout, cwd=cwd, env={**os.environ, **(env or {}), "LC_ALL": "C"},
        ).stdout
    except subprocess.CalledProcessError as error:
        raise VerificationError(f"Command failed ({error.returncode}): {arguments!r}\n{error.stderr}\n{error.stdout}") from error
    except (OSError, subprocess.TimeoutExpired) as error:
        raise VerificationError(f"Command failed: {arguments!r}: {error}") from error


def count_pdf_pages(path):
    output = run_command(["pdfinfo", Path(path).resolve()], timeout=120)
    match = re.search(r"^Pages:\s+(\d+)\s*$", output, re.MULTILINE)
    if not match or int(match.group(1)) < 1:
        raise VerificationError(f"pdfinfo did not report a positive page count for {path}: {output}")
    return int(match.group(1))


def validate_pdf_geometry(path, count):
    """Check each effective CropBox aspect and rotation before rasterization."""
    output = run_command(["pdfinfo", "-f", "1", "-l", str(count), Path(path).resolve()], timeout=120)
    sizes = re.findall(r"^Page\s+(\d+)\s+size:\s+(\S+)\s+x\s+(\S+)\s+pts", output, re.MULTILINE)
    rotations = re.findall(r"^Page\s+(\d+)\s+rot:\s+(-?\d+)\s*$", output, re.MULTILINE)
    expected = set(range(1, count + 1))
    if (len(sizes) != count or len(rotations) != count or {int(page) for page, _, _ in sizes} != expected
            or {int(page) for page, _ in rotations} != expected):
        raise VerificationError(f"pdfinfo did not report geometry for every PDF page in {path}")
    rotations = {int(page): int(rotation) for page, rotation in rotations}
    for page, width, height in sizes:
        width, height = float(width), float(height)
        rotation = rotations[int(page)]
        if rotation % 180:
            width, height = height, width
        # LibreOffice rounds its 960-point width to 960.009 points; this is geometry precision, not a pixel-diff exemption.
        if (rotation % 90 or not all(math.isfinite(value) and value > 0 for value in (width, height))
                or not math.isclose(width * CANVAS[1], height * CANVAS[0], rel_tol=1e-5)):
            raise VerificationError(f"PDF {path} page {page} effective geometry {width} x {height} at rotation {rotation} must be 16:9")


def render_pdf(path, output_dir, expected_count=65):
    """Rasterize every real PDF page with Poppler; discard stale frames."""
    count = count_pdf_pages(path)
    if count != expected_count:
        raise VerificationError(f"PDF {path} has {count} pages; expected {expected_count}")
    validate_pdf_geometry(path, count)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in output_dir.glob("page-*.png"):
        stale.unlink()
    renderer = shutil.which("pdftoppm") or shutil.which("pdftocairo")
    if not renderer:
        raise VerificationError("Missing Poppler renderer: install pdftoppm or pdftocairo")
    with tempfile.TemporaryDirectory(prefix=".render-", dir=output_dir) as temporary:
        prefix = Path(temporary) / "page"
        run_command([renderer, "-png", "-cropbox", "-scale-to", str(CANVAS[0]),
                     "-f", "1", "-l", str(count), Path(path).resolve(), prefix])
        frames = {}
        for frame in Path(temporary).glob("page-*.png"):
            match = re.fullmatch(r"page-(\d+)\.png", frame.name)
            if not match or int(match.group(1)) in frames:
                raise VerificationError(f"Unexpected renderer frame: {frame}")
            frames[int(match.group(1))] = frame
        if set(frames) != set(range(1, count + 1)):
            raise VerificationError(f"Renderer produced {len(frames)} pages; expected {count}")
        for page, frame in sorted(frames.items()):
            load_image(frame).close()
            frame.replace(output_dir / f"page-{page:03d}.png")
    return require_page_images(output_dir, expected_count)


def convert_pptx_to_pdf(path, output_dir):
    """Export the entire deck once, with a fresh isolated LibreOffice profile."""
    path, output_dir = Path(path).resolve(), Path(output_dir).resolve()
    if not path.is_file():
        raise VerificationError(f"Missing PPTX: {path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / "converted.pdf"
    destination.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix=".soffice-", dir=output_dir) as temporary:
        temporary = Path(temporary)
        export = temporary / "export"
        export.mkdir()
        output = run_command([
            "soffice", f"-env:UserInstallation={(temporary / 'profile').as_uri()}",
            "--headless", "--nologo", "--nodefault", "--nofirststartwizard",
            "--convert-to", "pdf:impress_pdf_Export", "--outdir", export, path,
        ], cwd=temporary, env={name: str(temporary) for name in ("TMPDIR", "TMP", "TEMP")})
        converted = export / f"{path.stem}.pdf"
        if not converted.is_file():
            raise VerificationError(f"LibreOffice did not create {converted}: {output}")
        converted.replace(destination)
    return destination


def make_contact_sheets(patterns, directories, output_dir):
    """Four patterns per sheet, with HTML/PDF/PPTX side by side."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    formats = ("html", "pdf", "pptx")
    pages = {name: require_page_images(directories[name], len(patterns)) for name in formats}
    for stale in output_dir.glob("contact-*.png"):
        stale.unlink()
    width, height, caption_height, rows = 400, 225, 36, 4
    font = ImageFont.load_default()
    sheets = []
    for start in range(0, len(patterns), rows):
        sheet = Image.new("RGB", (width * len(formats), (height + caption_height) * rows), "white")
        draw = ImageDraw.Draw(sheet)
        captions = []
        for row, pattern in enumerate(patterns[start:start + rows]):
            for column, name in enumerate(formats):
                x, y = column * width, row * (height + caption_height)
                image = load_image(pages[name][start + row])
                sheet.paste(image.resize((width, height), Image.Resampling.LANCZOS), (x, y))
                image.close()
                caption = f'{pattern["key"]} {pattern["id"]} | {name.upper()}'
                caption.encode("ascii")
                captions.append(caption)
                draw.multiline_text((x + 4, y + height + 4), "\n".join(textwrap.wrap(caption, width=55)), font=font, fill="black", spacing=2)
        metadata = PngInfo()
        metadata.add_text("captions", "\n".join(captions))
        destination = output_dir / f"contact-{len(sheets) + 1:02d}.png"
        sheet.save(destination, pnginfo=metadata)
        sheet.close()
        sheets.append(destination)
    return sheets


def compare_images(left, right):
    """Return raw RGB absolute pixel differences, normalized to 255."""
    difference = ImageChops.difference(load_image(left), load_image(right))
    channels = difference.split()
    nonzero = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
    return {
        "mean_absolute_difference": sum(ImageStat.Stat(difference).mean) / (3 * 255),
        "max_absolute_difference": max(high for low, high in difference.getextrema()) / 255,
        "different_pixel_fraction": 1 - nonzero.histogram()[0] / (CANVAS[0] * CANVAS[1]),
    }


def fingerprint(path):
    """Hash real bytes, or explicitly record an unavailable input."""
    path = Path(path)
    result = {"path": str(path), "sha256": None}
    try:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        result["sha256"] = digest.hexdigest()
    except OSError as error:
        result["error"] = f"Cannot read input {path}: {error}"
    return result


def compare_pages(report, directories):
    """Keep every numeric metric, including all pages after a mismatch."""
    for page in report["pages"]:
        filename = f'page-{page["page"]:03d}.png'
        for name, left, right in (("html_pdf", "html", "pdf"), ("pdf_pptx", "pdf", "pptx")):
            metric = compare_images(directories[left] / filename, directories[right] / filename)
            metric["passed"] = metric["mean_absolute_difference"] <= report["tolerance"]
            page[name] = metric
            if not metric["passed"]:
                report["errors"].append(f'{page["key"]} {page["id"]} {name}: mean absolute difference {metric["mean_absolute_difference"]:.9f} exceeds {report["tolerance"]}')
        page["passed"] = page["html_pdf"]["passed"] and page["pdf_pptx"]["passed"]
    report["max_mean_absolute_differences"] = {
        name: max(page[name]["mean_absolute_difference"] for page in report["pages"])
        for name in ("html_pdf", "pdf_pptx")
    }


def inspect_layout_receipt(receipt, path, manifest, html_dir, count):
    """Require a successful current audit bound to the source and every PNG."""
    prefix = f"Invalid layout receipt {path}"
    if not isinstance(receipt, dict) or receipt.get("schema_version") != 2:
        raise VerificationError(f"{prefix}: schema_version 2 is required")
    if (receipt.get("passed") is not True or receipt.get("errors") != []
            or type(receipt.get("issues")) is not int or receipt["issues"] != 0
            or any(type(receipt.get(name)) is not int or receipt[name] != count for name in ("expected", "checked"))):
        raise VerificationError(f"{prefix}: audit must pass with zero issues/errors and expected=checked={count}")

    def binding(record, expected, label):
        if (not isinstance(record, dict) or not isinstance(record.get("path"), str)
                or not Path(record["path"]).is_absolute() or not isinstance(record.get("sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", record["sha256"])):
            raise VerificationError(f"{prefix}: {label} needs an absolute path and SHA256 hash")
        if Path(record["path"]).resolve() != Path(expected).resolve():
            raise VerificationError(f"{prefix}: {label} path does not match the actual input")
        actual = fingerprint(record["path"])
        if actual["sha256"] != record["sha256"]:
            raise VerificationError(f"{prefix}: {label} hash does not match current bytes: {record['path']}")
        return actual

    inputs = receipt.get("inputs")
    html = receipt.get("html")
    if not isinstance(inputs, dict) or not isinstance(html, str) or not Path(html).is_absolute():
        raise VerificationError(f"{prefix}: source HTML and input bindings are required")
    source = binding(inputs.get("html"), html, "source HTML")
    binding(inputs.get("catalog"), manifest, "catalog")
    screenshots = receipt.get("screenshots")
    if not isinstance(screenshots, list) or len(screenshots) != count:
        raise VerificationError(f"{prefix}: exactly {count} unique screenshots are required")
    seen_pages, seen_paths = set(), set()
    for screenshot in screenshots:
        page = screenshot.get("page") if isinstance(screenshot, dict) else None
        if type(page) is not int or not 1 <= page <= count or page in seen_pages:
            raise VerificationError(f"{prefix}: screenshot page numbers must cover 1 through {count} uniquely")
        actual = binding(screenshot, Path(html_dir) / f"page-{page:03d}.png", f"screenshot page {page}")
        resolved = Path(actual["path"]).resolve()
        if resolved in seen_paths:
            raise VerificationError(f"{prefix}: duplicate screenshot input path {resolved}")
        seen_pages.add(page)
        seen_paths.add(resolved)
    return source


def reject_report_alias(output, sources):
    """Never overwrite an input with either a success or a failure report."""
    destination = (Path(output) / "artifact-report.json").resolve()
    for path in sources:
        source = Path(path).resolve()
        aliases = destination == source
        if not aliases:
            try:
                aliases = destination.samefile(source)
            except FileNotFoundError:
                pass  # An absent path cannot share an existing inode.
        if aliases:
            raise VerificationError("Artifact report destination overlaps an input; refusing any output mutation")


def prepare_output(directories, output, sources):
    """Remove stale owned evidence only after rejecting input/output aliases."""
    root = output.resolve()
    html = directories["html"].resolve()
    renders = [directories[name].resolve() for name in ("pdf", "pptx")]
    if len(set(renders)) != len(renders) or any(path.parent != root for path in renders):
        raise VerificationError("Render outputs overlap or escape the output directory")
    if any(html == path or path in html.parents for path in renders):
        raise VerificationError("HTML input and render output directories overlap")
    stale = list(output.glob("contact-*.png"))
    for name in ("pdf", "pptx"):
        stale.extend(directories[name].glob("page-*.png"))
    converted = directories["pptx"] / "converted.pdf"
    protected = {Path(path).resolve() for path in sources}
    if any(path.resolve() in protected for path in stale + [converted]):
        raise VerificationError("Input files overlap generated artifact outputs")
    for path in stale:
        path.unlink()
    converted.unlink(missing_ok=True)


def verify_exports(report, patterns, pdf, pptx, directories, output):
    count = report["expected_pages"]
    report["counts"]["html"] = len(require_page_images(directories["html"], count))
    report["counts"]["pdf"] = count_pdf_pages(pdf)
    report["pptx_inspection"] = inspect_pptx(pptx, expected_count=count)
    report["counts"]["pptx"] = report["pptx_inspection"]["slide_count"]
    for slide, pattern in zip(report["pptx_inspection"]["slides"], patterns):
        slide.update(key=pattern["key"], id=pattern["id"])
    render_pdf(pdf, directories["pdf"], expected_count=count)
    converted = convert_pptx_to_pdf(pptx, directories["pptx"])
    report["inputs"]["pptx_pdf"] = fingerprint(converted)
    report["counts"]["pptx_pdf"] = count_pdf_pages(converted)
    render_pdf(converted, directories["pptx"], expected_count=count)
    compare_pages(report, directories)
    sheets = make_contact_sheets(patterns, directories, output)
    report["contact_sheets"] = [str(path) for path in sheets]
    if len(sheets) != (count + 3) // 4:
        raise VerificationError(f"Incorrect contact sheet count: {len(sheets)}")


def verify_artifacts(pdf="pdf/science-tokyo-catalog.pdf", pptx="pptx/science-tokyo-catalog.pptx",
                     manifest="catalog/science-tokyo.json", output=".verification", html_dir=None,
                     tolerance=0.04, layout_report=None, *, expected_count=65):
    """Verify real exports. expected_count is a library seam for small unit fixtures only."""
    output = Path(output)
    directories = {name: output / name for name in ("html", "pdf", "pptx")}
    if html_dir is not None:
        directories["html"] = Path(html_dir)
    layout_report = Path(layout_report) if layout_report is not None else output / "layout-report.json"
    receipt, receipt_error = None, None
    try:
        receipt = json.loads(layout_report.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        receipt_error = f"Cannot read layout receipt {layout_report}: {error}"
    sources = [pdf, pptx, manifest, layout_report] + list(directories["html"].glob("page-*.png"))
    if isinstance(receipt, dict):
        records = list(receipt["inputs"].values()) if isinstance(receipt.get("inputs"), dict) else []
        records += receipt["screenshots"] if isinstance(receipt.get("screenshots"), list) else []
        sources += [record["path"] for record in records if isinstance(record, dict) and isinstance(record.get("path"), str)]
        if isinstance(receipt.get("html"), str):
            sources.append(receipt["html"])
    reject_report_alias(output, sources)
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1, "passed": False, "expected_pages": expected_count,
        "canvas": list(CANVAS), "tolerance": tolerance, "counts": {},
        "inputs": {name: fingerprint(path) for name, path in (("pdf", pdf), ("pptx", pptx), ("manifest", manifest), ("layout_report", layout_report))},
        "pages": [], "contact_sheets": [], "errors": [],
        "max_mean_absolute_differences": None,
        "renderer_note": "Raw RGB metrics include renderer/font antialiasing. No blur, alignment correction, or aliasing exemption is applied.",
    }
    try:
        if not math.isfinite(tolerance) or not 0 <= tolerance <= 0.04:
            raise VerificationError("Tolerance must be finite and between 0 and 0.04; do not loosen it to hide mismatches")
        prepare_output(directories, output, sources)
        patterns = load_patterns(manifest, expected_count=expected_count)
        report["counts"]["manifest"] = len(patterns)
        report["pages"] = [{"page": page, "key": pattern["key"], "id": pattern["id"],
                            "html_pdf": None, "pdf_pptx": None, "passed": False}
                           for page, pattern in enumerate(patterns, 1)]
        report["inputs"]["html"] = [dict(fingerprint(directories["html"] / f"page-{page:03d}.png"), page=page,
                                           key=pattern["key"], id=pattern["id"])
                                      for page, pattern in enumerate(patterns, 1)]
        required = [report["inputs"][name] for name in ("pdf", "pptx", "manifest")] + report["inputs"]["html"]
        unavailable = [item["error"] for item in required if "error" in item]
        if unavailable:
            raise VerificationError("\n".join(unavailable))
        if receipt_error:
            raise VerificationError(receipt_error)
        report["inputs"]["html_source"] = inspect_layout_receipt(receipt, layout_report, manifest, directories["html"], expected_count)
        verify_exports(report, patterns, pdf, pptx, directories, output)
        report["passed"] = not report["errors"] and all(page["passed"] for page in report["pages"])
    except (VerificationError, OSError, ValueError) as error:
        report["errors"].append(str(error))
    (output / "artifact-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8")
    return report


def tolerance_argument(value):
    try:
        number = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("tolerance must be numeric") from error
    if not math.isfinite(number) or not 0 <= number <= 0.04:
        raise argparse.ArgumentTypeError("tolerance must be finite and between 0 and 0.04")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, width=120))
    parser.add_argument("--pdf", type=Path, default=Path("pdf/science-tokyo-catalog.pdf"), help="Marp PDF export")
    parser.add_argument("--pptx", type=Path, default=Path("pptx/science-tokyo-catalog.pptx"), help="Marp picture-slide PPTX export")
    parser.add_argument("--manifest", type=Path, default=Path("catalog/science-tokyo.json"), help="65-pattern manifest in expected slide order")
    parser.add_argument("--output", "--out-dir", type=Path, default=Path(".verification"), help="report, renders, and isolated profiles directory")
    parser.add_argument("--html-dir", type=Path, help="HTML screenshot pages (default: OUTPUT/html)")
    parser.add_argument("--layout-report", type=Path, help="current schema-2 HTML layout receipt (default: OUTPUT/layout-report.json)")
    parser.add_argument("--tolerance", type=tolerance_argument, default=0.04, help="maximum normalized mean absolute RGB difference (may only be tightened)")
    arguments = vars(parser.parse_args(argv))
    try:
        report = verify_artifacts(**arguments)
    except (VerificationError, OSError, ValueError) as error:
        print(json.dumps({"passed": False, "errors": [str(error)]}))
        return 1
    print(json.dumps({"passed": report["passed"], "report": str(arguments["output"] / "artifact-report.json"),
                      "counts": report["counts"], "max_mean_absolute_differences": report["max_mean_absolute_differences"],
                      "errors": report["errors"]}, ensure_ascii=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
