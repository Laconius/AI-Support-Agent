# Sopoforix tenant pack

Plain idea: everything that makes this agent *Sopoforix* (not the shared engine).

| Path | Purpose |
|------|---------|
| `config.json` | Name, tagline, file pointers |
| `knowledge/` | Approved product / policy / sleep docs |
| `orders.json` | Demo orders (stand-in until a real store API) |

The shared code in `app/` loads this pack via `tenant.py` (`ACTIVE_TENANT=sopoforix` by default).

Later: add `tenants/another-brand/` and switch with an env var or request parameter.
