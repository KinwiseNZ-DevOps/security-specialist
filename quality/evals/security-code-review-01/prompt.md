---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Project context (nothing else is available to read): a Node.js API called billing-api (Express, Postgres via pg, Stripe webhooks) with routes under src/routes and a Dockerfile for deployment. Answer from this description and the code below.

src/routes/invoices.js has: app.get('/api/invoices/:id', async (req, res) => { const invoice = await Invoice.findById(req.params.id); res.json(invoice); });

Request: Review this route for security issues.
