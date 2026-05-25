# MITRE ATT&CK Integration (`integrations/mitre`)

Local CWE → ATT&CK technique lookup used to enrich `CVE_LOOKUP` responses.

## Runtime

Runtime code reads only the bundled index:

```text
data/knowledge_base/mitre_attack_index.json
```

```python
from integrations.mitre import MITREAttackCache

cache = MITREAttackCache.load_default()
techniques = cache.lookup_by_cwe(["CWE-502"])
```

## Refresh the index (offline)

Download the public Enterprise ATT&CK STIX bundle and rebuild the index:

```bash
python3 scripts/refresh_mitre_cache.py
```

Optional flags:

- `--url`: STIX bundle URL (defaults to MITRE CTI GitHub raw JSON)
- `--output`: output path for the generated index

## Index format

```json
{
  "CWE-502": [
    {"technique_id": "T1190", "name": "Exploit Public-Facing Application"}
  ]
}
```
