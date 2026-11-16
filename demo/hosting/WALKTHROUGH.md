# Walkthroughs for the interactive demo

Everything on screen is a recorded model output replayed locally. Say so once at the start. No baseline error is staged.

## 60-second judge walkthrough
1. **Open the file.** You land on a real claim with two parts and its source. Overall verdict: **Contradicted**. (5 s)
2. **Click “320 reviews”.** Only the review count in the source changes. Part 2 flips to **Supported** and so does the overall verdict. Click
   “323 reviews” to go back. Part 1 never moves. (15 s)
3. **Switch on “Show original binding bug”.** Two columns appear. Under the original rule the two quotes sit on the wrong parts, yet the overall
   verdict is the same. The line beneath gives the benchmark-wide effect: 5 of 754 verdicts, 153 part-level explanations. (15 s)
4. **Tab 2, switch “Enforce qualifiers” off.** A correct claim that was rejected becomes **Supported**. Pick “A wrong claim the rule blocks” and
   do the same: a wrong citation is let through. Totals beside it: 37 regained, 6 let through. (15 s)
5. **Tab 3.** The original certificate **passes** its audit although the evidence was on the wrong part. Flip the switch on the test copy and the
   checks **fail**. (10 s)

## Recording script (3–5 minutes)
| Time | Click | Expected on screen | Say |
|---|---|---|---|
| 0:00 | Open `Pramana_Bind_demo.html` | Tab 1; “323 reviews” selected; Part 1 Supported, Part 2 Contradicted; overall Contradicted; benchmark label REFUTES | “A model read this claim and this source and recorded which words bear on which part of the claim. A fixed rule turned that record into a verdict. These readings are recorded; the verdicts are recomputed in this browser.” |
| 0:25 | Point at the source | “323” outlined in red inside the amber highlight | “The claim says a rating above 85 percent, from fewer than 322 reviews. The source says 90 percent and 323 reviews. So part 2 fails, and the record says which words made it fail.” |
| 0:45 | Click **320 reviews** | “320” outlined; both parts Supported; overall Supported; label SUPPORTS | “This is the paired benchmark item. One number differs. Only part 2 changes.” |
| 1:00 | Click **323 reviews**, then switch on **Show original binding bug** | Two columns: Original rule: Part 1 Contradicted, Part 2 Supported, Overall Contradicted. Corrected rule: Part 1 Supported, Part 2 Contradicted, Overall Contradicted | “Our first rule counted claim parts from zero. The model counts from one. So each quote landed on the other part. Same overall verdict, wrong explanation. That happened on 153 of 754 items and changed only 5 verdicts.” |
| 1:35 | Open **Details** briefly, close it | Item id, certificate ids, offsets, the raw record | “Offsets, hashes and the full record are here for anyone who wants them.” |
| 1:50 | Tab **2 · Switch a rule off** | “Pink was born on September 8, 1979”; phrase “known professionally as Pink” highlighted; type necessary condition; verdict Not established; reference SUPPORTS | “The source plainly supports this. The model filed the stage name as a condition the claim leaves out, and the rule obeyed.” |
| 2:10 | Switch **Enforce qualifiers** off | Verdict Supported; note “not the signed certificate” | “Same reading, rule off, and it is accepted. The signed certificate is unchanged; this is a counterfactual.” |
| 2:25 | Switch it on; click **A wrong claim the rule blocks**; switch off | Not established → Supported; reference label Incorrect | “Here the rule is doing its job. The source limits which batches get gradients; the citing sentence drops that. Rule off, and a wrong citation gets through.” |
| 2:50 | Point at the bars | 37 correct claims regained; 6 wrong claims let through; 43 verdicts changed | “Across four benchmarks, the rule costs 37 correct acceptances and prevents 6 wrong ones. The diagnoses of why are our own reading, not an independent review.” |
| 3:10 | Tab **3 · What a passing audit certifies** | Support verdict Contradicted; Evidence assignment Wrong part; Audit result Pass; recorded steps all pass; three browser checks pass | “This is the original signed certificate. Its audit passes, because the audit replays the rule that was recorded, and that rule had the bug. An audit shows a result is reproducible and unaltered. It does not show the evidence was put on the right part.” |
| 3:40 | Switch on **Change “323 reviews” to “320 reviews” in the copy** | Audit result Fail; source hash, quotations and rule replay fail; recorded command-line result: hash chain fail | “This is a test copy, changed on purpose. Now the checks fail. The commands to repeat both audits are below.” |
| 4:05 | Show Figure 2 of the report | — | “On four public benchmarks the typed verifier accepted 29 of 402 unsupported claims against 40 for asking directly, and recovered 188 of 352 supported claims against 218. More cautious, not more accurate, and no clear advantage over generic structure. What it adds is a decision someone else can replay and challenge.” |
