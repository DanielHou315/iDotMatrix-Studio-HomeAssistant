# Contributing

Thanks for helping. Bug reports, panel test results and pull requests are all welcome. If you
own a panel size or firmware we have not tested, a report of what works is valuable too.

The project rules for humans and coding agents alike are in [`AGENTS.md`](AGENTS.md); this file
covers the practical steps.

## Set up

You need [uv](https://docs.astral.sh/uv/) and Node.js (only for a syntax check). Nothing else is
installed into your system.

```sh
git clone https://github.com/DanielHou315/iDotMatrix-Studio-HomeAssistant.git
cd iDotMatrix-Studio-HomeAssistant
```

## Checks

CI runs these on every pull request; run them before you push.

```sh
uv run --with pytest --with pillow python -m pytest -q tests          # tests
uvx ruff check --select E,F,B,UP --ignore E501 custom_components tests scripts  # lint
node --check custom_components/idm_studio/frontend/panel.js           # panel syntax
python3 scripts/release.py check                                      # version and changelog agree
```

CI also runs Home Assistant's `hassfest` and the HACS validator. To run hassfest locally:

```sh
docker run --rm -v "$PWD/custom_components:/github/workspace/custom_components:ro" ghcr.io/home-assistant/hassfest
```

## Try it in Home Assistant

Copy `custom_components/idm_studio` into `<config>/custom_components/` and restart Home Assistant.
A restart is needed after every Python change; after a `panel.js` change a browser reload is
enough. For debug logs:

```yaml
logger:
  logs:
    custom_components.idm_studio: debug
```

Close the phone app first: the panel accepts one Bluetooth connection at a time.

## Where things are

- `protocol.py` builds the Bluetooth packets and `media.py` frames images and scores how well they
  fit. Both are pure Python with no Home Assistant imports, so they are unit tested directly.
- `device.py` owns the Bluetooth connection, `runtime.py` the actions and state of one panel.
- `frontend/panel.js` is the sidebar page, a single web component with no build step.
- [`docs/architecture.md`](docs/architecture.md) explains the data flow and records protocol
  findings from real panels. Add to it when you learn something about the firmware.

Protocol changes need a test, and ideally a note on which panel size and firmware they were
tried on. Behaviour differs between sizes: for example 16×16 panels crash on text drawn in
16×32 cells.

## Pull requests

- Branch off `main` (`feat/*`, `fix/*`, `chore/*`, `docs/*`) and open the PR against `main`.
- Commit messages: `type(scope): summary`, with `type` one of `feat`, `fix`, `chore`, `docs`,
  `test`, `refactor`.
- Add a line under **Unreleased** in [`CHANGELOG.md`](CHANGELOG.md) for changes users would
  notice.
- Do not change the version in a feature or fix PR; releases do that.

## Releases

Maintainers release from `main`:

1. Create a branch `chore/release-vX.Y.Z` and run `python3 scripts/release.py bump X.Y.Z`. It
   updates `VERSION` and `manifest.json` and turns the **Unreleased** changelog section into the
   release's section.
2. Commit as `chore(release): vX.Y.Z` and open a PR.
3. Merge it. The release workflow tags `vX.Y.Z` and publishes a GitHub release with the changelog
   section as notes. HACS users are offered the update.

Versions follow [Semantic Versioning](https://semver.org/): breaking changes to actions, entities
or stored data bump the major version (minor while below 1.0).

## License

By contributing you agree that your contribution is licensed under the
[GPL-3.0](LICENSE), like the rest of the project.
