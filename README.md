# OpenClaw Agent Admin

Adaptador Python y skill para administrar agentes persistentes de OpenClaw
mediante la CLI oficial `openclaw agents`.

## Incluye

- Alta: `create`
- Consulta: `list` y `get`
- Cambios de identidad y bindings: `update`
- Baja física confirmada: `delete --confirm`
- Salida JSON, `--dry-run` y pruebas sin dependencias externas

## Uso rápido

```bash
python3 skills/openclaw-agent-admin/scripts/manager.py list
python3 skills/openclaw-agent-admin/scripts/manager.py create cliente-001 \
  --workspace ~/.openclaw/workspaces/cliente-001 \
  --agent-dir ~/.openclaw/agents/cliente-001/agent \
  --model openai/gpt-5.6-luna
python3 skills/openclaw-agent-admin/scripts/manager.py update cliente-001 --emoji "🧠"
python3 skills/openclaw-agent-admin/scripts/manager.py delete cliente-001 --confirm
```

El adaptador no modifica directamente `openclaw.json`, SQLite, workspaces ni
credenciales; delega esas operaciones en la CLI instalada de OpenClaw.

## Pruebas

```bash
python3 -m unittest discover -s skills/openclaw-agent-admin/tests -v
```
