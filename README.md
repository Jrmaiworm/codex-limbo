<p align="center">
  <img src="assets/coin-banner.svg" alt="codex-limbo — my precious tokens" width="100%">
</p>

<p align="center">
  <strong>Um pequeno tesouro para acompanhar seus tokens do Codex.</strong><br>
  Histórico, cotas, alertas e estimativas diretamente no terminal, com dados locais.
</p>

<p align="center">
  <a href="LICENSE"><img alt="Licença MIT" src="https://img.shields.io/badge/licen%C3%A7a-MIT-C99B48?style=flat-square"></a>
  <img alt="Python 3.11 ou superior" src="https://img.shields.io/badge/Python-3.11%2B-DFB45E?style=flat-square">
  <img alt="Linux e Windows" src="https://img.shields.io/badge/sistemas-Linux%20%7C%20Windows-9B7138?style=flat-square">
  <a href="https://github.com/Jrmaiworm/codex-limbo/actions/workflows/windows.yml"><img alt="Teste no Windows" src="https://img.shields.io/github/actions/workflow/status/Jrmaiworm/codex-limbo/windows.yml?branch=main&label=Windows&style=flat-square"></a>
</p>

> **My precious tokens.** Saiba quanto consumiu antes que a cota desapareça nas sombras.

## ⚔️ Comece sua jornada

**Linux / Ubuntu** — cole no terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/jrmaiworm/codex-limbo/main/install.sh | bash
```

**Windows** — cole no PowerShell:

```powershell
irm https://raw.githubusercontent.com/jrmaiworm/codex-limbo/main/install.ps1 | iex
```

Abra um novo terminal depois da instalação e execute `codex-limbo doctor`. Os instaladores configuram [uv](https://docs.astral.sh/uv/getting-started/installation/) e Python 3.11 quando necessário; não exigem `pipx`, Git ou privilégios de administrador. No Linux, `curl` é necessário para baixar o script.

## 🪙 O que há no tesouro

| Comando | O que mostra |
| --- | --- |
| `codex-limbo status` | Cota restante, resets, créditos disponíveis e tokens locais. |
| `codex-limbo history --hours 6` | Consumo com gráfico em blocos; aceita 1, 3, 6, 12 ou 24 horas. |
| `codex-limbo watch --seconds 30` | Atualização contínua, velocidade e previsão quando houver dados suficientes. |
| `codex-limbo alerts` | Avisos para consumo, queda de cota e esgotamento estimado. |
| `codex-limbo advice` | Comparação de uso por modelo e sugestões estimadas. |
| `codex-limbo doctor` | Diagnóstico dos arquivos locais, sem abrir credenciais. |

Exemplo rápido:

```text
$ codex-limbo status
codex 5h: 72.0% remaining; reset 2026-09-23 19:53; credits unavailable
Tokens today: 128,400; last hour: 12,300 (local estimates)
Local token rate: 205.0/min
```

O exemplo é ilustrativo. Os números reais vêm das sessões da sua máquina.

## 🧭 De onde vêm os números

O programa lê eventos de tokens e cota em `~/.codex/sessions` e `~/.codex/archived_sessions`. Salva apenas identificadores de sessão, horários, nomes de projeto e modelo, contadores numéricos e snapshots de cota em SQLite. Reimportações substituem registros com a mesma sessão e horário.

| Sistema | Banco SQLite | Configuração |
| --- | --- | --- |
| Linux | `~/.local/share/codex-limbo/usage.sqlite3` | `~/.config/codex-limbo/config.toml` |
| Windows | `%LOCALAPPDATA%\codex-limbo\usage.sqlite3` | `%APPDATA%\codex-limbo\config.toml` |

Use `CODEX_HOME` para apontar para outra pasta do Codex. No Linux, `XDG_DATA_HOME` e `XDG_CONFIG_HOME` também são respeitados.

<details>
<summary>Configurar os alertas</summary>

Crie o arquivo de configuração indicado acima:

```toml
[alerts]
token_threshold = 100000
period_minutes = 60
quota_drop_percent = 15.0
exhaustion_minutes = 60
watch_seconds = 30
```

Os alertas aparecem somente no terminal.

</details>

## 🔒 A moeda fica com você

- Nenhum prompt, resposta, arquivo de trabalho, cookie ou credencial é salvo no banco ou enviado a servidores.
- `doctor` verifica a existência do arquivo de autenticação, sem ler seu conteúdo.
- As cotas são snapshots registrados localmente pelo Codex. Podem estar ausentes ou desatualizadas, e seu formato depende de interfaces não públicas.
- Tokens, velocidade, previsão de esgotamento e custo-benefício são **estimativas locais**; não equivalem necessariamente à cobrança ou à cota oficial.
- Não há reset automático de cota.

## 🛠️ Desenvolver

Requer Python 3.11+:

```bash
python -m pip install -e '.[test]'
pytest
```

O pacote também pode ser instalado de um checkout local com `pipx install .`.

---

<p align="center"><em>Uma moeda para contar todos os tokens.</em></p>
