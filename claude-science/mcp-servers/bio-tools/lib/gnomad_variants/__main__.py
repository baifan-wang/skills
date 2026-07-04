"""CLI: python -m gnomad_variants <method> [args...] -- minimal JSON output."""
import json
import sys

from .tool import GnomadVariants


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: python -m gnomad_variants <method> key=value ...", file=sys.stderr)
        return 2
    method, *pairs = argv
    kwargs = {}
    for p in pairs:
        k, _, v = p.partition("=")
        if v.isdigit():
            v = int(v)
        kwargs[k] = v
    tool = GnomadVariants()
    fn = getattr(tool, method, None)
    if fn is None:
        print(f"unknown method {method}", file=sys.stderr)
        return 2
    print(json.dumps(fn(**kwargs), indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
