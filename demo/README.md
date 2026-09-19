# Synthetic demo scenario

`scenario.json` is the canonical public playground scenario. It is deliberately
fictional and must remain safe to publish. The live demo reads these
assumptions once at startup, then generates a deterministic stream of synthetic
transactions while it runs.

To try another scenario without editing Python:

```sh
python3 app.py --demo --scenario demo/scenario.json
```

The loader requires `synthetic: true` and validates the required fields. Do not
put bank credentials, real people, real account identifiers, or private data in
this directory.
