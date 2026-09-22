# Official Jev call entry

## Background and goal

`POST /v1/functions/:key/invoke` only accepts the business `input` of a published function. The user needs a second entry: the local service keeps the TypeSafe key, the caller authenticates with a client token, sends `{model, state, questions}` per the official contract, and the workbench forwards it to TypeSafe.

Completion level: functional. Without a key the production service returns `PROVIDER_NOT_CONFIGURED`; a real cloud round trip is not required this round.

## Scope

- Production gains `POST /v1/systemone` and `GET /v1/models`.
- Clients gain an explicit `official_invoke` capability, off by default. Only a token with it set may use these two routes.
- The upstream address is fixed to `https://api.typesafe.ai`; callers cannot change it.
- Judgment functions, publishing, function grants, and the MCP/Pi tool contract are unchanged.
- Demo mode (`JEV_MODE=demo`) refuses both routes, so a simulation is never recorded as an official success.

## Non-goals

- No custom upstream, and no accepting the caller's own TypeSafe key.
- No mixing official pass-through into `/v1/functions/:key/invoke`.
- No raw tool for MCP or Pi.
- Never write raw state, questions, or answers to runs, logs, or Git.

## Call contract

`POST /v1/systemone`, bearer client token.

```json
{
  "model": "jev-1.13.0",
  "state": "Please refund the duplicate charge.",
  "questions": {
    "is_billing": {
      "type": "noul",
      "instructions": "Is this a billing or refund question?"
    }
  }
}
```

On success the official `{model, answers, usage}` is returned verbatim, with an `x-request-id` response header. Errors keep this product's `{error:{code,message}, meta}` shape; an upstream 401 must never be reported as `INVALID_CLIENT_TOKEN`.

`GET /v1/models` requires the same `official_invoke` capability and forwards the official model list.

## Grants and isolation

- `official_invoke` can be toggled when creating or editing a client. It is independent of function grants, so a token may have the official entry and no functions at all.
- Not granted: 403 `OFFICIAL_INVOKE_FORBIDDEN`.
- After the token is revoked both routes return 401.
- A client token still cannot reach `/api/admin`.
- The migration adds the column to existing databases with a default of 0 and does not reset existing clients.

## Records

Runs may record request_id, client_id, model, usage, duration, error code, and `diagnostic_meta.official=true`. function_id and version are empty. Question and answer bodies are never stored.

Concurrency and timeouts reuse the Invoker's gate and its 30s budget.

## Acceptance

- A token without the flag gets 403 from `/v1/systemone` and `/v1/models`; with the flag and a fixture it returns the official answers shape and stores no bodies.
- Function invoke is unaffected; a client with no function grants but `official_invoke=true` can still use the official entry.
- Demo mode returns 409 `DEMO_MODE`; a production provider with no key returns 503 `PROVIDER_NOT_CONFIGURED`.
- The migration preserves existing clients with `official_invoke=0`.
- The admin page can set the capability when creating a credential, and the English copy exists.

Verify: `pnpm typecheck`; `pnpm test`; `pnpm test:e2e` (the existing story must not break because the flag defaults off).
