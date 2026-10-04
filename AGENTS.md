# AGENTS.md: whitepapers

Instructions for AI coding agents (Grok, Cursor, Claude Code, Codex, Copilot and others) working **in** this repo or **using it as a building block**. Humans: see [README.md](README.md).

## What this is

Index of the 79 historic whitepapers in the Blockchain Lab PDF library (Bitcoin, Ethereum, Ripple, Stellar, Corda…) as README table, index.json and index.csv; links point at the original files on blockchainlab.com, refreshed weekly.

- Kind: dataset, docs · stability: `stable` · licence: NOASSERTION
- Machine-readable manifest: [`blocks.json`](blocks.json) (schema: [BLOCKS-SCHEMA](https://github.com/Blockchains/.github/blob/main/docs/BLOCKS-SCHEMA.md))
- How it fits with the other Blockchains repos: [Build with Blocks](https://github.com/Blockchains/.github/blob/main/docs/BUILD-WITH-BLOCKS.md)

## Setup

```bash
python3 --version
```

## Build and test

```bash
python3 scripts/build_index.py   # rebuild from blockchainlab.com sitemaps + /pdf page
```

Tests hit **live** public networks/APIs (the org rule is no mocks). A failure can be an upstream outage: re-run before changing code.

## Structure

| Path | What |
|---|---|
| `index.json, index.csv` | the index |
| `README.md` | table |
| `scripts/build_index.py` | generator |

## Conventions

- Year from the corpus record, else filename (marked †), else blank.

## Extension points

- Improve metadata extraction in `scripts/build_index.py`.

## Do

- Link to originals.

## Don't

- Commit PDF files.
- Commit secrets, keys or `.env` files. Run `gitleaks` before pushing; CI and the org policy reject leaks.

## Using it from another project

- **index.json** (file): `https://raw.githubusercontent.com/Blockchains/whitepapers/main/index.json`
- **index.csv** (file): `index.csv`

See the README section [Use as a building block](README.md#use-as-a-building-block) for a copy-paste example.

## Related blocks

- [Blockchains/blockchainlab-api](https://github.com/Blockchains/blockchainlab-api): the `whitepapers` dataset covers the larger research corpus (600+)
- [Blockchains/blockchainlab-mcp](https://github.com/Blockchains/blockchainlab-mcp): `search_whitepapers` tool
