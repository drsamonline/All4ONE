# Security

All4one runs locally and sends nothing anywhere. There is no telemetry, no update
check and no network call except the ones you explicitly run (the Network tools).

## Reporting

Open a private security advisory on this repository, or email the author. Please do
not open a public issue for a vulnerability.

## Design notes

- External programs are invoked with argument lists, never through a shell string.
- Archive extraction validates every entry path and refuses anything that would
  escape the destination folder (zip-slip / tar-slip).
- Tools that delete or overwrite data are marked `destructive`, ask for confirmation
  in the UI, and preview their plan before acting where a preview is meaningful.
- Optional dependencies are probed, never installed automatically.
- The settings file holds your theme, favourites and recent tools. Nothing else.
