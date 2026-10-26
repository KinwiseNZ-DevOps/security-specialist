---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Project context (nothing else is available to read): a repository with a PHP application. Its Dockerfile starts with FROM php:8.3-apache, composer.json requires php ^8.2, and composer.lock exists. Answer from this description. Today is 22 October 2026.

Request: Which PHP versions are affected by CVE-2026-109618 and is anyone exploiting it?
