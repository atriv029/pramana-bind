# Repository history note

Before publication the commit history was rewritten once, on 16 November 2026, for three reasons: to set the author identity, to remove
automated attribution lines from commit messages, and to remove a blind-review answer key that had been committed. File contents are otherwise
unchanged and every commit keeps its original date. Because commit identifiers are hashes of their content, they changed. Documents written during
the sprint cite the earlier identifiers; this table maps them.

| Identifier cited in sprint documents | Identifier in this repository | Date (UTC) | What it is |
|---|---|---|---|
| `8585439` | `f7169f2` | 2026-11-14 08:39 | first checkpoint |
| `be19aa1` | `d8bfb69` | 2026-11-14 08:46 | support status separated from verdict |
| `beb6cf7` | `87c216f` | 2026-11-14 08:58 | **Experiment 1 freeze** (data, prompts, scorer, protocol) |
| `8714fdf` | `e3aa4d2` | 2026-11-14 09:02 | documentation and tooling |
| `1ddef2c` | `d2a180c` | 2026-11-14 12:18 | Experiment 1 results (tag `exp1-frozen`) |
| `8224cb2` | `ad7a2c9` | 2026-11-15 06:31 | **Experiment 2 freeze** |
| `275d763` | `ed1ac43` | 2026-11-15 07:42 | Experiment 2 results as registered (tag `exp2-frozen`) |
| `9423f8b` | `c173ae9` | 2026-11-16 04:14 | part-binding fix; second-model freeze |
| `fc1e82e` | `647aa25` | 2026-11-16 04:31 | human review, reconciliation, corrected results |

The freeze commits precede the first held-out model call of each experiment; call timestamps are not stored in the call logs, so the ordering
rests on the run configuration files and these commit dates. The factual statement of AI assistance is in the report (Appendix D).
