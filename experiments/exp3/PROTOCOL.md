# Experiment 3: second-model replication (frozen 2026-11-16T04:14:45Z, before any call on these files with this model)

Question: does the method effect seen with claude-haiku-5-5 (structured methods accept fewer unsupported claims and
recover fewer supported ones than a direct judge) appear with a second model?

- **Model:** claude-sonnet-5-5 through the same headless Claude Code interface, default sampling, no tools, same
  system line, 240 s timeout, 2 transport retries. It is a larger model from the **same vendor family**; no model from
  another family was reachable (the only other configured endpoints are the owner's own RunPod deployments, scaled to
  zero, which were not modified). The served identifier reported by each call is recorded and checked.
- **Systems:** B0 (direct judge), B1 (generic structured), N1 (revised method); one call each; prompts byte-identical
  to Experiment 2 (hashes in experiments/exp2/PROTOCOL.md). The taxonomy judge is omitted for time.
- **Decision rules:** N1/3.2 and B1/1.1 (the part-binding fix, made and tested before this run; not tuned on any result).
- **Sample:** chosen by seed 20261116 as whole source families from the Experiment 2 evaluation files, before any
  call: contractnli 68 items / 4 families (sha256 4ee00ffbceb5); vitaminc 86 items / 25 families (sha256 95c83ee3d7f7); scicite 76 items / 6 families (sha256 d8c26fafbc51); attributionbench 56 items / 50 families (sha256 b18044ef71dd). Total 286 items, 858 calls.
- **Scoring:** experiments/exp2/score.py unchanged. Per dataset; false support, supported recall, three-way accuracy
  where available; family-cluster bootstrap for N1 minus B0. The same items scored for claude-haiku-5-5 (from its
  recorded replies, same rules) give the comparison; an exploratory model-by-method interaction is the difference of
  the two N1-minus-B0 differences, resampling families.
- **Stopping:** all 858 calls or a usage-limit failure; in the latter case only completed datasets are reported and the
  shortfall is stated. Failed calls are re-issued once; malformed replies are scored as failures.
- This run is exploratory replication on a subsample, not a registered primary analysis.
