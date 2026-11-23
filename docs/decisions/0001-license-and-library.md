# 0001: GPL-3.0, and original built-in art

**License.** The protocol was learned from GPL-3.0 projects (python3-idotmatrix-library and the
tukies integration), and we verify against them, so the integration is GPL-3.0 too.

**Built-in library.** The official app's GIF library is proprietary and has no license that allows
redistribution, so it is not shipped. `scripts/make_library.py` generates original procedural
animations instead; they are part of this repository under its license. Third-party packs (for
example CC0 ones) can be added later, each with its license recorded in `library/index.json`.
