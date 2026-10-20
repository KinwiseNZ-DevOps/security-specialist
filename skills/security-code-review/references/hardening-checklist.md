# Hardening checklist and templates

Quick-reference templates for what a fix should look like, and a master checklist for a full review pass.

## Security headers (Express, via helmet)

```typescript
import helmet from 'helmet';

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
      frameAncestors: ["'none'"],
      objectSrc: ["'none'"],
      baseUri: ["'self'"],
      formAction: ["'self'"],
    },
  },
  hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
  frameguard: { action: 'deny' },
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
}));
app.disable('x-powered-by');
```

Other frameworks set the same headers through their own middleware or reverse proxy; the header names and values above apply regardless of framework.

## JWT validation checklist

1. Verify the signature with the expected algorithm; reject `alg: none`.
2. Enforce the algorithm explicitly (for example `algorithms: ['RS256']`), rather than accepting whatever the token claims.
3. Check `exp` and reject an expired token.
4. Check `iat` and reject a token issued implausibly far in the past.
5. Check `aud` and reject a token not meant for this service.
6. Check `iss` and reject a token from an unknown issuer.
7. Store the token in an httpOnly cookie, not `localStorage`.
8. Use a short-lived access token (minutes, not days) with refresh-token rotation.
9. Rotate signing keys periodically.

## Secure cookie flags

```
Set-Cookie: session=value; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=3600
```

| Flag | Purpose | When to use it |
|---|---|---|
| `HttpOnly` | Not readable from JavaScript, so XSS cannot steal it | Always |
| `Secure` | Only sent over HTTPS | Always |
| `SameSite=Strict` | Only sent on same-site requests; strongest CSRF protection | Auth and session cookies |
| `SameSite=Lax` | Sent on top-level navigation; needed for flows like OAuth redirects | Cookies that must survive a cross-site top-level navigation |
| `Path=/` | Limits where the cookie is sent | Always, set deliberately |
| `Max-Age` | An explicit expiry, preferred over `Expires` | Always |

## Master checklist

**Authentication and sessions**: passwords hashed with argon2id or bcrypt at a real cost factor; JWTs signed with RS256 or ES256 with the algorithm enforced on verify; access tokens short-lived; refresh tokens one-time-use and rotated; rate limiting on login, registration and password reset; the session regenerated after login; MFA available for privileged accounts.

**Authorization**: every endpoint has auth middleware; every resource access has an ownership check; authorization is enforced server-side, never only in the frontend; mass assignment is prevented by explicit field selection; sensitive operations require re-authentication.

**Input and output**: all user input validated server-side; all database operations parameterised; HTML output sanitised before rendering user content; error responses do not expose stack traces in production.

**Secrets**: no hardcoded secret in source; `.env` files in `.gitignore`; no server secret exposed to the client bundle; environment variables validated at startup rather than failing silently later.

**Headers**: Content-Security-Policy configured, nonce-based where practical; Strict-Transport-Security with preload; `X-Content-Type-Options: nosniff`; `X-Frame-Options: DENY`; a restrictive Referrer-Policy; a restrictive Permissions-Policy; CORS limited to known origins.

**Dependencies**: an audit command passing in CI; the lockfile committed and verified (for example `npm ci`); new dependencies reviewed for typosquatting and unexpected install scripts; no wildcard or "latest" version pins in production.

**Logging**: security events (auth failures, access denied, rate-limit hits) logged; no sensitive data in logs; structured logging with a correlation ID per request.
