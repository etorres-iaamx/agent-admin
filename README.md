# OpenClaw Agent Admin y Hermes Profile Admin

Este repositorio contiene administradores Python y skills separadas para
OpenClaw y Hermes. Cada skill administra una plataforma diferente y debe
invocarse únicamente para el sistema que le corresponde.

## Componentes

```text
skills/openclaw-agent-admin/SKILL.md
skills/openclaw-agent-admin/scripts/manager.py
skills/openclaw-agent-admin/tests/test_manager.py

skills/hermes-profile-admin/SKILL.md
tools/hermes_profiles/manager.py
tests/test_hermes_profiles.py
```

## OpenClaw

El administrador de OpenClaw delega el ciclo de vida en la CLI oficial:

```bash
python3 skills/openclaw-agent-admin/scripts/manager.py list
python3 skills/openclaw-agent-admin/scripts/manager.py create cliente-001 \
  --workspace ~/.openclaw/workspaces/cliente-001 \
  --agent-dir ~/.openclaw/agents/cliente-001/agent \
  --model <provider/model-configurado>
python3 skills/openclaw-agent-admin/scripts/manager.py update cliente-001 --emoji "🧠"
python3 skills/openclaw-agent-admin/scripts/manager.py delete cliente-001 --confirm
```

Reemplaza `<provider/model-configurado>` por un modelo disponible en el
entorno de OpenClaw. Las opciones `--bindings` y `--tree` de `list` dependen
de la versión instalada; compruébalas con `openclaw agents list --help`.

No modifica directamente `openclaw.json`, SQLite, workspaces ni credenciales.

## Hermes

El administrador de Hermes delega el ciclo de vida en `hermes profile` y
administra únicamente los archivos de contexto del Profile indicado:

```bash
python3 tools/hermes_profiles/manager.py list
python3 tools/hermes_profiles/manager.py show cliente-001
python3 tools/hermes_profiles/manager.py create cliente-001 \
  --description "Atencion Comercial"
python3 tools/hermes_profiles/manager.py validate cliente-001
python3 tools/hermes_profiles/manager.py context-update cliente-001 \
  --soul-file ./SOUL.md \
  --user-file ./USER.md \
  --agents-file ./AGENTS.md
python3 tools/hermes_profiles/manager.py delete cliente-001 --confirm
```

El administrador de Hermes:

- No clona `default` ni otro Profile.
- Protege `default` contra eliminación.
- Restringe las escrituras a `~/.hermes/profiles/<name>/` o `HERMES_HOME`.
- Administra `SOUL.md`, `memories/USER.md` y `AGENTS.md` mediante archivos
  explícitos.
- Incluye `--dry-run` para revisar mutaciones.
- No modifica bases de datos, sesiones, canales ni credenciales.

El Gateway de Hermes sigue siendo compartido por los Profiles; este script no
inicia un Gateway independiente por cliente.

## Pruebas

```bash
python3 -m unittest discover -s tests -p 'test_hermes_profiles.py' -v
python3 -m unittest discover -s skills/openclaw-agent-admin/tests -v
```

No se versionan tokens, contraseñas, API keys, archivos `.env` ni estados
locales.
