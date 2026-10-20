# Secret and credential detection patterns

Load this during the secrets and exposure scan step.

## High-confidence patterns

These almost always indicate a real secret:

**API keys and tokens** (as regular expressions): OpenAI `sk-[a-zA-Z0-9]{48}`; Anthropic `sk-ant-[a-zA-Z0-9\-_]{90,}`; AWS access key `AKIA[0-9A-Z]{16}`; GitHub token `gh[pousr]_[a-zA-Z0-9]{36,}` or `github_pat_[a-zA-Z0-9]{82}`; Stripe `sk_live_[a-zA-Z0-9]{24,}` or `rk_live_[a-zA-Z0-9]{24,}`; Twilio `AC[a-z0-9]{32}` (account SID) or `SK[a-z0-9]{32}` (API key); SendGrid `SG\.[a-zA-Z0-9\-_.]{66}`; Slack `xoxb-`, `xoxp-` or `xapp-` followed by numeric and alphanumeric segments; Google API key `AIza[0-9A-Za-z\-_]{35}`; Google OAuth client ID ending `.apps.googleusercontent.com`; Mailgun `key-[a-zA-Z0-9]{32}`.

**Private keys and certificates**: `-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY( BLOCK)?-----`, `-----BEGIN CERTIFICATE-----`.

**Database connection strings with an embedded password**: `mongodb(+srv)?://user:password@...`, `postgres://` / `postgresql://` / `mysql://` with a password segment, `redis://:password@...`, or any string containing `connection_string`, `connstr` or `db_url` alongside `password=`.

**Hardcoded passwords by variable name**: a variable named `password`, `passwd`, `pwd`, `secret`, `api_key`, `apikey`, `auth_token`, `access_token` or `private_key` assigned a literal string of 8 or more characters.

## Entropy-based detection

For a string literal over 20 characters in an assignment context, calculate its Shannon entropy. Above roughly 4.5 bits per character combined with that length is a likely secret even when the variable name gives no hint. Exclude known false positives: lorem ipsum filler text, HTML or CSS content, base64-encoded non-sensitive configuration (still worth a lower-severity note), and UUIDs (high entropy but a recognisable, non-secret format).

## Files that should never be committed

Flag these if they exist in the repository or are tracked by git: `.env` and its `.local` / `.production` / `.staging` variants, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa`, `id_ed25519`, `credentials.json`, `service-account.json`, `gcp-key.json`, `secrets.yaml`, `secrets.json`, `config/secrets.yml`. Also check whether `.gitignore` actually covers these patterns; a secret-shaped filename that is not ignored is itself a finding.

## CI/CD and infrastructure-as-code risks

**GitHub Actions**: a literal value in an `env:` block instead of `${{ secrets.NAME }}`; a step that echoes a secret (`run: echo ${{ secrets.MY_SECRET }}`), which leaks it to the build log.

**Docker**: a secret baked into `ENV` (persists in every image layer) or passed as a build `ARG` (visible in image history).

**Terraform**: a literal password or access key in a resource block instead of a variable or data source reference.

## Safe patterns: do not flag these

Recognise intentional placeholders and skip them: `"your-api-key-here"`, `"<YOUR_API_KEY>"`, `"${API_KEY}"`, `"${process.env.API_KEY}"`, `os.environ.get('API_KEY')`, `"REPLACE_WITH_YOUR_KEY"`, `"xxx...xxx"`, and an example key shown in documentation or a comment.
