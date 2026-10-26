---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Project context (nothing else is available to read): a Node.js API called billing-api (Express, Postgres via pg, Stripe webhooks) with routes under src/routes and a Dockerfile for deployment. Answer from this description and the code below.

src/config/stripe.js assigns the Stripe secret key as a literal string hardcoded in source (starting with the live-mode prefix), instead of reading it from an environment variable.

Request: Scan this file.
