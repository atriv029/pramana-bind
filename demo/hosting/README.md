# Hosting the Pramāṇa-Bind demo

`index.html` in this folder is the whole demo: one file, about 270 KB, with its data and fonts inside it. It makes no network requests, needs no
API key and calls no model. It is byte-identical to `Pramana_Bind_demo.html`.

## Use it without hosting
Double-click `index.html` (or `Pramana_Bind_demo.html`). It opens in any current browser, online or offline.

## Host it (optional)
Any static host works. Upload **only `index.html`** so that it sits at the root of the site.
- **GitHub Pages:** put `index.html` in the repository root or in `docs/`, then Settings → Pages → deploy from that branch and folder. The link is
  `https://<user>.github.io/<repository>/`.
- **Netlify Drop, Cloudflare Pages, Vercel:** drag this folder onto the upload area. The link they give you is the demo link.

## If the sprint portal takes a link instead of an attachment
1. Host `index.html` as above and copy the public link.
2. Paste that link into the portal's optional demo / other-artifacts field (and, if you wish, into the “Other artifacts” line of the report's
   Code and Data section before exporting the PDF again).
3. The report PDF is submitted separately and does not depend on the demo being hosted.

## Check before sharing
Open the link in a private window. Tab 1 should start on the 323-review case with the overall verdict “Contradicted”.
`node demo/interactive/test_demo.js <absolute path to index.html>` re-runs the automated check (offline, all controls, no console errors).

## What is recorded and what is computed
- **Recorded:** the model's readings (extractions), the benchmark labels, and the command-line audit output shown in tab 3.
- **Computed in the browser:** quote location, the binding of evidence to claim parts, the verdict under each rule version, the qualifier
  counterfactual, and (tab 3) the SHA-256 of the source text. The hash chain and signature are **not** verified in the browser.
