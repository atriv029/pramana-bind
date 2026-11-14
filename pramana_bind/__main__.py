"""CLI: keygen | sign | audit | crosscheck. None of these calls a model."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import certificate as c


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="pramana_bind")
    sub = ap.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("keygen"); k.add_argument("key", type=Path)
    s = sub.add_parser("sign"); s.add_argument("ledger", type=Path); s.add_argument("key", type=Path)
    a = sub.add_parser("audit"); a.add_argument("ledger", type=Path)
    a.add_argument("--pubkey", help="trusted signer key (base64), obtained out-of-band")
    a.add_argument("--checkpoint", help="SEQ:HASH of a head you saw earlier (detects rollback)")
    a.add_argument("--json", action="store_true")
    x = sub.add_parser("crosscheck"); x.add_argument("--per-class", type=int, default=100)
    args = ap.parse_args(argv)

    if args.cmd == "keygen":
        print(c.generate_key(args.key))
    elif args.cmd == "sign":
        print(json.dumps(c.sign_head(args.ledger, c.load_key(args.key)), indent=1))
    elif args.cmd == "crosscheck":
        from .crosscheck import crosscheck_closed
        r = crosscheck_closed(args.per_class)
        print(json.dumps(r, indent=1))
        return 0 if not r["disagreements"] else 1
    else:
        cp = None
        if args.checkpoint:
            n, h = args.checkpoint.split(":", 1)
            cp = (int(n), h)
        rep = c.audit(args.ledger, args.pubkey, checkpoint=cp)
        if args.json:
            print(json.dumps(rep.to_dict(), indent=1))
        else:
            for st in rep.steps:
                where = f" seq {st.seq}" if st.seq is not None else ""
                print(f"{'PASS' if st.ok else 'FAIL'}  {st.step}{where}  {st.detail}")
            print(f"{'INTEGRITY AND REPLAY CHECKS PASSED' if rep.ok else 'AUDIT FAILED'}: "
                  f"{rep.n_certificates} certificates, {rep.n_events} events")
            if rep.ok:
                print("This does not assert that the extracted interpretation of the source is correct.")
        return 0 if rep.ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
