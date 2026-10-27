"""Isolated LibreOffice -> PDF -> Poppler export, with content lineage checks."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from PIL import Image

from . import IDS, MANIFEST_NAME, mapping
from .source import validate_source
from .drawing import WIDTH, HEIGHT

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCRATCH = ROOT / ".verification/diagrams"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(command, *, env=None):
    result = subprocess.run(list(map(str, command)), capture_output=True, text=True,
                            check=True, timeout=240, env=env)
    return result.stdout.strip()


def expected_pngs(directory):
    expected = {f"{name}.png" for name in IDS}
    found = {p.name for p in Path(directory).glob("*.png")}
    if found != expected:
        raise ValueError(f"PNG count/mapping mismatch: missing={sorted(expected-found)}, "
                         f"unexpected={sorted(found-expected)}")


def check_exports(source, output_dir):
    """Read-only check. A changed source OR a changed/missing image is stale."""
    counts = validate_source(source)
    output_dir = Path(output_dir)
    manifest = json.loads((output_dir / MANIFEST_NAME).read_text())
    if manifest.get("schema") != 1:
        raise ValueError("Unsupported diagram manifest schema")
    if manifest["source"]["sha256"] != sha256(source):
        raise ValueError("Stale source: PPTX hash differs from exported PNG manifest; run --export-only")
    images = manifest["images"]
    expected_pngs(output_dir)
    if [{k: row[k] for k in ("id", "slide", "file")} for row in images] != mapping():
        raise ValueError("Manifest image IDs/order mismatch")
    for row in images:
        path = output_dir / row["file"]
        if sha256(path) != row["sha256"]:
            raise ValueError(f"Stale or corrupted image: {path.name}")
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            if im.width < 1600 or abs(im.height/im.width-HEIGHT/WIDTH) > .001:
                raise ValueError(f"Wrong resolution/aspect: {path.name}: {im.size}")
            if [im.width, im.height] != [row["width"], row["height"]]:
                raise ValueError(f"Manifest dimensions mismatch: {path.name}")
    return {"slides": len(counts), "images": len(images), "source_sha256": sha256(source),
            "native_shapes": sum(c["shapes"] for c in counts),
            "charts": sum(c["charts"] for c in counts), "verified": True}


def export_source(source, output_dir, *, width=2000, scratch=DEFAULT_SCRATCH):
    if width < 1600:
        raise ValueError("PNG width must be at least 1600 pixels")
    source, output_dir, scratch = Path(source).resolve(), Path(output_dir).resolve(), Path(scratch).resolve()
    counts = validate_source(source)
    for executable in ("soffice", "pdfinfo", "pdftoppm"):
        if not shutil.which(executable):
            raise RuntimeError(f"Missing export executable: {executable}")
    output_dir.mkdir(parents=True, exist_ok=True)
    unexpected = {p.name for p in output_dir.glob("*.png")} - {f"{n}.png" for n in IDS}
    if unexpected:
        raise ValueError(f"Unexpected PNG files; refusing to delete or silently ignore: {sorted(unexpected)}")
    scratch.mkdir(parents=True, exist_ok=True)
    before = sha256(source)
    with tempfile.TemporaryDirectory(prefix="export-", dir=scratch) as tmp:
        stage = Path(tmp)
        (stage / "tmp").mkdir()
        env = dict(os.environ, TMPDIR=str(stage/"tmp"), TEMP=str(stage/"tmp"), TMP=str(stage/"tmp"))
        profile = (stage/"profile").as_uri()
        run(["soffice", f"-env:UserInstallation={profile}", "--headless", "--convert-to",
             "pdf:impress_pdf_Export", "--outdir", stage, source], env=env)
        pdf = stage / f"{source.stem}.pdf"
        if not pdf.is_file() or pdf.stat().st_size < 1000:
            raise RuntimeError("LibreOffice returned without creating a nonempty PDF")
        info = run(["pdfinfo", pdf], env=env)
        match = re.search(r"^Pages:\s+(\d+)", info, re.M)
        if not match or int(match.group(1)) != len(IDS):
            raise RuntimeError(f"PDF needs exactly 22 pages: {info}")
        run(["pdftoppm", "-png", "-scale-to-x", width, "-scale-to-y", -1,
             pdf, stage/"page"], env=env)
        pages = sorted(stage.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
        if len(pages) != len(IDS):
            raise RuntimeError(f"Poppler exported {len(pages)} PNGs, expected 22")
        images = []
        for row, page in zip(mapping(), pages):
            with Image.open(page) as im:
                im.load()
                if im.width != width or abs(im.height/im.width-HEIGHT/WIDTH) > .001:
                    raise RuntimeError(f"Wrong rendered image dimensions: {page.name}: {im.size}")
                images.append(dict(row, width=im.width, height=im.height, sha256=sha256(page)))
        if sha256(source) != before:
            raise RuntimeError("Source changed during export; refusing mixed-source output")
        manifest = {"schema": 1, "source": {"file": source.name, "sha256": before},
                    "canvas_inches": [WIDTH, HEIGHT], "slides": counts, "images": images,
                    "renderer": {"soffice": run(["soffice", "--version"], env=env),
                                 "poppler": subprocess.run(["pdftoppm", "-v"], capture_output=True,
                                    text=True, check=True, env=env).stderr.splitlines()[0]}}
        # Only publish after every page has rendered and passed structural checks.
        for row, page in zip(images, pages):
            os.replace(page, output_dir/row["file"])
        manifest_file = stage/MANIFEST_NAME
        manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
        os.replace(manifest_file, output_dir/MANIFEST_NAME)
        shutil.copyfile(pdf, scratch/"last-render.pdf")
    return check_exports(source, output_dir)
