# Language and framework patterns

Load the section matching the detected language after Step 1 (Detect). Each snippet is a pattern to search for, not a complete rule; read enough surrounding code to confirm it is really exploitable.

## JavaScript / TypeScript (Node.js, React, Next.js, Express, Angular)

Critical APIs to flag wherever user input can reach them: `eval()`, `new Function('return ...')`, `child_process.exec()`, and any `fs.readFile` / `fs.writeFile` call whose path includes user input.

**Express**: no `helmet()` (missing security headers); `express.json()` with no size limit (denial of service risk); `cors({ origin: '*' })` or `cors({ origin: req.headers.origin })` (reflects any origin); `app.set('trust proxy', true)` when the app is not actually behind a known proxy.

**React**: `dangerouslySetInnerHTML={{ __html: userContent }}` (XSS unless sanitised); `<a href={userUrl}>` where `userUrl` could be a `javascript:` URL.

**Next.js**: a server action or API route with no auth check before a sensitive action; an API route handler with no method check, so a GET-only handler also accepts POST.

**Angular**: `bypassSecurityTrust(Html|Script|Style|Url|ResourceUrl)` called on anything derived from user input, without sanitising it with DOMPurify first; a `JitCompilerFactory` compiling a user-controlled template string; an `HttpInterceptor` chain that does not attach the auth token centrally, leaving some requests unauthenticated by omission.

## Python (Django, Flask, FastAPI)

**Django**: `User.objects.raw(f"SELECT * FROM users WHERE name = '{name}'")` (SQLi); `@csrf_exempt` on anything other than a token-authenticated API; `DEBUG = True` in a production settings file (exposes stack traces); a default or placeholder `SECRET_KEY`; `ALLOWED_HOSTS = ['*']`.

Beyond those, Django's own advisory history (20 years of entries at [docs.djangoproject.com/en/stable/releases/security/](https://docs.djangoproject.com/en/stable/releases/security/), check that page for anything after this was written) repeats a small set of recurring risk classes more often than any single bug. Treat the framework's own safety as conditional on these, not automatic:

- **ORM structural-input injection.** Parameterisation protects a *value*, not a column name, lookup name, alias, sort field or `Q` connector. User input reaching `order_by()`, `annotate()`/`aggregate()`/`extra()`, `values()`/`values_list()`, a `FilteredRelation` alias, or the `_connector` kwarg of a `Q` object has repeatedly produced SQL injection even though the query itself uses the ORM. Never pass user input into any of these except as a plain filter value; validate a field or column name against an explicit allowlist first.
- **Unbounded string processing as a denial-of-service vector.** Django's own "safe" helpers, `Truncator`, `strip_tags()`, `urlize()`, `floatformat()`, `intcomma`, and validator regexes, have repeatedly been exploitable through catastrophic backtracking or unbounded work when run on a long, attacker-controlled string with no length cap. Length-limit user input before it reaches a template filter or validator, especially on a public, unauthenticated form.
- **Upload and archive path traversal.** A filename from an upload, or an entry name inside an uploaded archive, can carry `../` or an absolute path; `Storage.save()` and `archive.extract()` have both been exploitable this way more than once. Reduce to a basename and confirm the resolved path still sits inside the intended directory, even when using Django's own storage API.
- **Trusting the `Host` header.** Cache poisoning, CSRF bypass and leaked password-reset links have all come from code (framework or application) that trusted the `Host` header beyond what `ALLOWED_HOSTS` validates. Do not build an absolute URL or a cache key from the raw header.
- **Caching a response that varies by user.** `UpdateCacheMiddleware` and `cache_page` have repeatedly leaked one user's private data (a CSRF token, a `Set-Cookie`, authenticated content) to another when a view's output depends on `request.user` or a cookie but the cache key or `Vary` header did not account for it.
- **Timing-based account enumeration.** A different response time or status code between "the account exists" and "it does not" (password reset, login, a password hasher upgrade path) has repeatedly let an attacker enumerate real accounts. These paths need to look and take the same time either way.
- **Admin widget XSS.** Several admin widgets (a raw-id widget, a URL field's "current value" link, `readonly_fields`, a related-object popup) have rendered a model or user-supplied value unescaped. Treat admin-rendered output with the same suspicion as any other template output.
- **Validator newline injection.** `URLValidator`, `DomainNameValidator` and similar have at times accepted an embedded newline, so a value that "passed validation" could still carry an injected header into an outgoing request or response. Passing a validator is not the same as being safe to interpolate into a header.

**Flask**: `app.run(debug=True)` in production; a weak or default `app.secret_key`; `eval(request.args.get('expr'))`; `render_template_string(f"Hello {name}")` (server-side template injection).

**FastAPI**: a route with no `Depends(get_current_user)` equivalent on a sensitive operation; a file-serving route that builds the path directly from a request parameter (path traversal).

## Java (Spring Boot)

String-concatenated SQL passed to `jdbcTemplate.query()`; a `DocumentBuilderFactory` with external entity resolution not explicitly disabled (XXE); `ObjectInputStream.readObject()` on untrusted input with no allowlist (insecure deserialization); `.antMatchers("/admin/**").permitAll()`; `management.endpoints.web.exposure.include=*` exposing all actuator endpoints.

## PHP

Direct interpolation of `$_GET` / `$_POST` into a query string; `include($_GET['page'] . ".php")` (local or remote file inclusion); `eval($_POST['code'])`; `extract($_POST)` (can overwrite any variable in scope); `==` instead of `===` for a password or token comparison; `unserialize($_COOKIE['data'])` (can lead to remote code execution depending on available gadget classes). Also check the PHP version itself: see [runtime-and-platform-advisories.md](runtime-and-platform-advisories.md).

## Go

`exec.Command("sh", "-c", userInput)`; string-built SQL passed to `db.Query()`; a file path built with `filepath.Join` on unsanitised user input; `tls.Config{InsecureSkipVerify: true}` outside a throwaway test; `math/rand` used anywhere security-relevant instead of `crypto/rand`.

## Ruby on Rails

`User.where("name = '#{params[:name]}'")` (use `User.where("name = ?", params[:name])` instead); `@user.update(params[:user])` without `params.require(:user).permit(...)` (mass assignment); `eval(params[:code])` or `send(params[:method])` with user input; `redirect_to params[:url]` (open redirect); `YAML.load(user_input)` (use `YAML.safe_load`).

## Dart and Flutter

Published CVEs against the Dart and Flutter ecosystem (checked via the NVD, since GitHub's own advisory database for `flutter/flutter` currently lists none) cluster into a few mobile-specific classes worth checking beyond the general patterns above:

- **Deep links and custom URI schemes are untrusted input.** A Flutter app's URI-scheme handler or FFI bridge can be invoked by any other app or a crafted link, not only by the app's own UI. A handler that performs a privileged action (changing a setting, running a command, importing a config) without checking where the call actually came from is exploitable the same way an unauthenticated endpoint is; treat every parameter a deep link carries as hostile.
- **A content URI's display name is not a safe filename.** On Android, `DISPLAY_NAME` from a `ContentResolver` (as used by file picker plugins) can be set by whatever app or file supplied the URI, including `../` segments. Never build a filesystem path from it directly; reduce it to a basename and confirm the resolved path stays inside the intended directory.
- **An HTTP client following a redirect can leak an `Authorization` header cross-origin.** A Dart HTTP client (or an adapter such as an HTTP/2 adapter) that copies the original request's headers onto a redirected request without checking whether the redirect target is the same host can hand a bearer token or basic-auth credential to a different server. Confirm the client strips or re-validates sensitive headers on a cross-origin redirect.
- **Package extraction is archive extraction.** `dart pub` / `flutter pub` fetching and unpacking a package is the same path-traversal risk as any other archive extraction (see the upload and archive traversal pattern under Django, which is not Django-specific); a malicious package name or archive entry could escape the intended install directory in an unpatched client.
- **A generated or scaffolded Dart backend can ship an insecure default.** Backend frameworks built for the Dart/Flutter ecosystem (for example Serverpod) have shipped a weak password hashing algorithm and a generated HTTP client that skipped TLS certificate validation. Check a generated server's auth and networking defaults the same way you would hand-written code; "it was generated" is not evidence it is safe.
- **A URL parsed two different ways in the same system can disagree.** Dart's URI class historically parsed a backslash differently from the WHATWG URL standard that browsers use, so a URL judged safe by one parser could be interpreted differently by the other, enabling an auth bypass. Where a URL crosses between Dart code and a browser or another language's parser, do not assume both sides agree on its meaning.

## Rust

An `unsafe` block with no comment explaining why it is sound; `a + b` on values that could overflow in a financial or security-relevant calculation (use `checked_add` or `saturating_add`); `.unwrap()` or `.expect()` on a `Result` or `Option` in a code path that handles untrusted input, which panics instead of returning an error; deserializing untrusted bytes with a format that is not designed for untrusted input (review the format's own security notes before trusting it).
