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

**Flask**: `app.run(debug=True)` in production; a weak or default `app.secret_key`; `eval(request.args.get('expr'))`; `render_template_string(f"Hello {name}")` (server-side template injection).

**FastAPI**: a route with no `Depends(get_current_user)` equivalent on a sensitive operation; a file-serving route that builds the path directly from a request parameter (path traversal).

## Java (Spring Boot)

String-concatenated SQL passed to `jdbcTemplate.query()`; a `DocumentBuilderFactory` with external entity resolution not explicitly disabled (XXE); `ObjectInputStream.readObject()` on untrusted input with no allowlist (insecure deserialization); `.antMatchers("/admin/**").permitAll()`; `management.endpoints.web.exposure.include=*` exposing all actuator endpoints.

## PHP

Direct interpolation of `$_GET` / `$_POST` into a query string; `include($_GET['page'] . ".php")` (local or remote file inclusion); `eval($_POST['code'])`; `extract($_POST)` (can overwrite any variable in scope); `==` instead of `===` for a password or token comparison; `unserialize($_COOKIE['data'])` (can lead to remote code execution depending on available gadget classes).

## Go

`exec.Command("sh", "-c", userInput)`; string-built SQL passed to `db.Query()`; a file path built with `filepath.Join` on unsanitised user input; `tls.Config{InsecureSkipVerify: true}` outside a throwaway test; `math/rand` used anywhere security-relevant instead of `crypto/rand`.

## Ruby on Rails

`User.where("name = '#{params[:name]}'")` (use `User.where("name = ?", params[:name])` instead); `@user.update(params[:user])` without `params.require(:user).permit(...)` (mass assignment); `eval(params[:code])` or `send(params[:method])` with user input; `redirect_to params[:url]` (open redirect); `YAML.load(user_input)` (use `YAML.safe_load`).

## Rust

An `unsafe` block with no comment explaining why it is sound; `a + b` on values that could overflow in a financial or security-relevant calculation (use `checked_add` or `saturating_add`); `.unwrap()` or `.expect()` on a `Result` or `Option` in a code path that handles untrusted input, which panics instead of returning an error; deserializing untrusted bytes with a format that is not designed for untrusted input (review the format's own security notes before trusting it).
