#!/usr/bin/env python3
"""Native editable PPTX -> isolated LibreOffice PDF -> 22 contained PNG assets.

Default: regenerate source AND export (overwrites generated source).
--export-only: export existing source, preserving manual edits byte-for-byte.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from science_tokyo_diagrams import mapping, SOURCE_NAME
from science_tokyo_diagrams.source import generate_source
from science_tokyo_diagrams.export import check_exports, export_source, DEFAULT_SCRATCH

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "assets/science-tokyo/diagrams"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--list", action="store_true", help="Print stable ID/slide/PNG mapping")
    modes.add_argument("--generate-only", action="store_true", help="Regenerate native source, without rendering")
    modes.add_argument("--export-only", "--export-existing", dest="export_only", action="store_true",
                       help="Render existing PPTX; NEVER regenerate or rewrite it")
    modes.add_argument("--check", action="store_true", help="Read-only source/PNG lineage validation")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source", type=Path, help="Existing source PPTX (only --export-only or --check)")
    parser.add_argument("--width", type=int, default=2000, help="PNG width, at least 1600 (default: 2000)")
    parser.add_argument("--scratch-dir", type=Path, default=DEFAULT_SCRATCH)
    args = parser.parse_args()
    if args.source and not (args.export_only or args.check):
        parser.error("--source is only valid with --export-only or --check")
    source = args.source or args.output_dir/SOURCE_NAME
    try:
        if args.list:
            result = mapping()
        elif args.check:
            result = check_exports(source, args.output_dir)
        else:
            if not args.export_only:
                counts = generate_source(source)
            if args.generate_only:
                result = {"source": str(source), "slides": len(counts),
                          "native_shapes": sum(c["shapes"] for c in counts)}
            else:
                result = export_source(source, args.output_dir, width=args.width,
                                       scratch=args.scratch_dir)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as exc:
        detail = f"; stderr: {exc.stderr}" if isinstance(exc, subprocess.CalledProcessError) else ""
        print(f"Diagram build failed: {exc}{detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
