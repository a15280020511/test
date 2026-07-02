# Maintenance Mode

The system uses a daily-operations mode.

Inputs:

- plugin registry: `configs/plugins.json`
- dependency list: `pyproject.toml`
- workflows: `.github/workflows`

Checks:

- plugin registry exists
- full dependency install works
- health check works
- cleanup workflow exists
- WebGPT contract is valid

Outputs:

- markdown report
- json artifact

Boundary:

Routine checks and reports are automated. If an upstream package changes its public interface in a breaking way, CI reports the failure and the code must be repaired.
