# Access-Stack site deployment

The static website lives in `site/` and is intentionally build-tool-free.

## Cloudflare Pages

Create a Pages project connected to this GitHub repository and use:

- Production branch: `main`
- Framework preset: None
- Build command: leave blank
- Build output directory: `site`

After the first deployment, attach the custom domain `www.access-stack.com` (and optionally redirect the apex `access-stack.com` to `www.access-stack.com`).

The `site/_headers` file configures static security headers supported by Cloudflare Pages.

## Local preview

From the repository root:

```bash
python3 -m http.server 8080 --directory site
```

Then open `http://127.0.0.1:8080`.

## Content sources

The website copy is derived from the repository's current README and `FINDINGS.md`. Pilot findings are deliberately labeled preliminary and should be updated as sample sizes and evaluation methods change.

## Security notes

- Do not place API keys, tokens, credentials, `.env` files, private reports, or identity documents under `site/`.
- Keep the public site static unless a server-side feature is genuinely needed.
- Review security headers when adding third-party scripts, analytics, forms, external fonts, or embedded content.
