# ThreadMilling

Simple Python thread-milling G-code generator.

## Project layout

- `thread_milling.py` - core `ThreadMilling` class (GUI/CLI reusable)
- `thread_milling_cli.py` - interactive CLI
- `ThreadMilling.py` - compatibility launcher to CLI

## Run

```powershell
python thread_milling_cli.py
```

GUI:

```powershell
python thread_milling_gui.py
```

GUI flow:

- click `Generate Preview` to review the G-code
- click `Save G-code` to write the preview to disk

or legacy launcher:

```powershell
python ThreadMilling.py
```

Install GUI dependency:

```powershell
python -m pip install PySide6
```

If you provide a hole file, it parses hole positions and parameters.
If you leave the hole file blank, it uses conversational prompts for:
- internal/external
- top_down/bottom_up
- depth
- major diameter
- pitch
- cutter diameter

Default thread hand is right-hand.

## Notes

- Top-down + right-hand defaults to `G2` helix.
- Bottom-up + right-hand defaults to `G3` helix.
- Left-hand thread flips arc direction.

## GitHub release build

When a GitHub Release is published (for example for tag `v1.0.0`), workflow
`.github/workflows/release-windows-onefile.yml` builds a Windows one-file GUI executable:

- output path: `dist/ThreadMillingGUI.exe`
- uploads workflow artifact: `ThreadMillingGUI-windows-onefile`
- attaches executable to the GitHub Release for that tag
