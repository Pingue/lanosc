# QLC+ dummy workspace (QLC+ 5.x)

This folder contains a minimal QLC+ workspace for LANOSC dummy testing:

- `lanosc-dummy-qlc5.qxw`
- `lanosc-dummy-osc.qxi`

## What it includes

- Function `Dummy A` (ID `0`)
- Function `Dummy B` (ID `1`)
- A Virtual Console page with two buttons bound to those functions

## Load in QLC+

1. Open QLC+ 5.x.
2. Import `lanosc-dummy-osc.qxi` in Input/Output → Input Profiles (create/import profile), then assign it to your OSC input universe.
3. Load `lanosc-dummy-qlc5.qxw`.

If your QLC+ build doesn't show an import button for profiles, install it manually:

```bash
mkdir -p ~/.qlcplus/inputprofiles
cp qlcplus/lanosc-dummy-osc.qxi ~/.qlcplus/inputprofiles/
```

Then restart QLC+ and select profile `lanosc Dummy OSC` on your OSC input universe.

## OSC profile channels

The bundled OSC profile defines two button channels:

- Channel 1: `/lanosc/dummy/a`
- Channel 2: `/lanosc/dummy/b`

These names match LANOSC dummy events.

## Map to controls/functions

Use Input/Output monitoring to confirm incoming OSC hits channels 1 and 2, then bind:

- Channel 1 to `Dummy A` (function ID `0`) or VC button `Dummy A`
- Channel 2 to `Dummy B` (function ID `1`) or VC button `Dummy B`

## Notes

LANOSC currently emits these OSC addresses:

- `/lanosc/dummy/a`
- `/lanosc/dummy/b`

If needed, adjust `lanosc.toml` playbacks to keep these paths aligned.
