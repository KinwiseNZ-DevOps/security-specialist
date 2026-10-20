# Vulnerability categories: deep reference

Detailed detection guidance for every vulnerability category. OWASP references point to the 2021 Top 10 category letters (A01 to A10); use them as a cross-reference, not a severity rating.

## 1. Injection flaws

### SQL injection
Look for string concatenation or interpolation inside queries, raw `.query()` / `.execute()` / `.raw()` calls with variables, ORM `whereRaw()` / `selectRaw()` with user input, and second-order SQLi (data stored safely, then used unsafely later).

```
"SELECT ... " + variable
`SELECT ... ${variable}`
f"SELECT ... {variable}"
cursor.execute("... " + input)
```

Safe pattern: parameterised queries (`db.query('SELECT * FROM users WHERE id = ?', [userId])`) or an ORM's own safe finder.

Escalation check: is the query's result ever used in another query (second-order), or is a table or column name itself user-controlled (cannot be parameterised; must be allowlisted)?

### Cross-site scripting (XSS)
Look for `innerHTML`, `document.write()`, `dangerouslySetInnerHTML` (React), `v-html` (Vue), `bypassSecurityTrustHtml` (Angular), unescaped template output, and DOM-based sinks (`location.hash`, `document.referrer`, `window.name` written to the page). Sanitise with a library such as DOMPurify before rendering user-controlled HTML; never with a bespoke regex.

### Command injection
Node: `exec(userInput)`, `execSync(\`ping ${host}\`)`, `spawn('sh', ['-c', userInput])`. Python: `os.system(user_input)`, `subprocess.call(user_input, shell=True)`. PHP: `exec($input)`, `` `$input` ``. Safe alternative: the array form of spawn or subprocess, without a shell, plus an allowlist of permitted commands.

### Server-side request forgery (SSRF)
Flag any outbound HTTP request where the URL is user-controlled (webhooks, URL preview, image fetch, PDF generation). High-risk targets: cloud metadata endpoints (`169.254.169.254`), `localhost`, `127.0.0.1`, and private ranges (`10.x.x.x`, `192.168.x.x`).

### Path traversal
```
filename = request.args.get('file')
open(f'/var/uploads/{filename}')   # ../../../../etc/passwd
```
Safe pattern: take only the base name, join it to the fixed upload directory, and confirm the resolved path still starts with that directory before opening it.

### Template injection and XXE
Template injection: user input rendered through a template engine without escaping (`render_template_string(f"Hello {name}")`). XXE: an XML parser that has not disabled external entity resolution.

## 2. Authentication and access control

### Broken object-level authorization (BOLA / IDOR)
A resource ID taken straight from the URL or params without an ownership check, especially with sequential, guessable IDs.
```
// vulnerable: no ownership check
const doc = await Document.findById(req.params.id);
// safe: verify ownership in the same query
const doc = await Document.findOne({ _id: req.params.id, owner: req.user.id });
```

### JWT weaknesses
`alg: "none"` accepted; a weak or hardcoded secret; no `exp` check; algorithm confusion (an RS256 token accepted as HS256); the token stored in `localStorage` instead of an httpOnly cookie. `jwt.decode()` does not verify a signature; confirm the code calls `jwt.verify()` with an explicit `algorithms` array.

### Missing authentication or authorization
Admin or sensitive endpoints with no auth middleware, a route registered before the auth middleware is applied, a debug endpoint left exposed, or a GraphQL resolver missing a field-level check.

### CSRF
A state-changing request (POST, PUT, DELETE) with no CSRF token, or a session cookie with no `SameSite` attribute.

## 3. Secrets and sensitive data

See [secret-patterns.md](secret-patterns.md) for the detection patterns themselves. In this category, also flag: a full user object (including password hash or other sensitive fields) returned from an API, a stack trace exposed in a production error response, and sensitive values printed to logs.

## 4. Cryptography

| Algorithm | Issue | Replace with |
|---|---|---|
| MD5 | Broken for security use | SHA-256, or bcrypt/argon2 for passwords |
| SHA-1 | Collision attacks | SHA-256 |
| DES / 3DES | Weak key size | AES-256-GCM |
| RC4 | Broken | AES-GCM |
| ECB mode | No IV, patterns visible in ciphertext | GCM, or CBC with a random IV |

Weak randomness: `Math.random()` or `Date.now()` used for a token is predictable; use `crypto.randomBytes()` (Node) or `secrets.token_urlsafe()` (Python). Password hashing: never a fast hash (MD5, SHA family) alone; use bcrypt or argon2 with a real work factor.

## 5. Business logic

Race conditions (check-then-act without a transaction or lock, especially around balances or inventory), missing rate limiting on login, 2FA, password reset or other sensitive or expensive endpoints, and predictable resource identifiers.

## 6. Headers

Missing or misconfigured response headers are IMPORTANT severity unless noted; all map to OWASP A02.

- Missing `Content-Security-Policy`, or one that allows `unsafe-inline` / `unsafe-eval` (prefer a nonce-based policy).
- Missing `Strict-Transport-Security` (`max-age=31536000; includeSubDomains; preload`).
- Missing `X-Content-Type-Options: nosniff`.
- Missing `X-Frame-Options: DENY` (and `frame-ancestors 'none'` in the CSP).
- A permissive `Referrer-Policy` (use `strict-origin-when-cross-origin`).
- Missing `Permissions-Policy`.
- CORS wildcard origin combined with `credentials: true`: CRITICAL, since it lets any site make authenticated requests on the user's behalf.

## 7. Frontend

- Unsanitised HTML rendering (`innerHTML`, `v-html`, `dangerouslySetInnerHTML`) without DOMPurify: CRITICAL.
- `eval()` or other dynamic code evaluation on user input: CRITICAL; use a structured parser such as `JSON.parse` instead.
- `postMessage` listeners that do not check `event.origin`.
- Prototype pollution: user input merged into an object via `Object.assign`, `__proto__`, or `constructor.prototype` without filtering keys.
- Open redirect: a redirect target taken from a query parameter without confirming it is a relative, same-site path.
- Sensitive data (tokens, session IDs) written to `localStorage` instead of an httpOnly cookie.
- Client-only validation with no equivalent check on the server.

## 8. API

- A new endpoint with no rate limiter, especially one that is expensive or sends email or SMS.
- GraphQL without query depth or complexity limiting.
- File upload with no type or size check.
- A webhook handler that does not verify the sender's signature.
- An API response that leaks internal details (stack traces, raw SQL, query plans).
- `express.json()` or an equivalent body parser with no size limit (denial of service risk).

## 9. AI and LLM security

- Prompt injection: user input concatenated directly into a prompt string, rather than passed as a separate user message with a fixed system instruction.
- LLM output passed to a database query, shell command, or template without the same validation and parameterisation as any other untrusted input. An LLM's output is not safer than a user's.
- No schema validation on a structured LLM response before it drives application logic; validate against an explicit schema and reject anything that does not match.

## 10. Logging

- Security-relevant events (auth failures, access denied, rate-limit hits, password changes) not logged at all.
- Sensitive values (passwords, tokens, PII) written to logs in plain text; use a logger with field redaction.
- Log entries built by string concatenation of user input, which allows log injection; use structured (for example JSON) logging instead.

## Framework-specific notes

- **Next.js / React server actions**: a `'use server'` function with no session or role check is a CRITICAL finding, equivalent to an unauthenticated endpoint. A client component reading `process.env` directly (not via a `NEXT_PUBLIC_` variable) will not have the value at build time, but check that no secret was put behind a name that was meant to be public. A server component passing a full database object into a client component can leak fields the client was never meant to see; pick only the needed fields first.
- **Express**: missing `helmet()` and `app.disable('x-powered-by')`; a session cookie set without `httpOnly`, `secure` and `sameSite`; an error handler that returns `err.stack` outside development.
- **Go**: `math/rand` used for a token, key or anything security-relevant (use `crypto/rand`); `tls.Config{InsecureSkipVerify: true}` in anything that is not a throwaway test.
