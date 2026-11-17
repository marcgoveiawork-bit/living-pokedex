# Living Pokédex

Single-page site: `index.html` (home grid + entry view, hash-routed), images in `assets/`.

## Rules for every new entry (set by the owner)

1. **Verify the data against the real Pokédex** before adding: number, name, species category,
   types, height, weight, abilities (incl. hidden) and all six base stats. Use the current-generation
   values (separate Sp. Atk / Sp. Def), not Gen I "Special", and not Mega/regional forms.
   Descriptions are written fresh, never copied from game text.
2. **Check the depth map for image distortion and fix as much as possible.** Run
   `python3 tools/prep_depth.py assets/<name>.png <raw-depth> assets/<name>-depth.png`, overlay the
   result on the photo to confirm the outline lines up, then screenshot the entry with the mouse at
   the far left and far right and look for tearing or halos around the silhouette.
   If the depth tool missed part of the subject (flame, smoke), add `--fill x0,y0,x1,y1` around it.
   If a part reads far too near (e.g. a flame brighter than the tail it sits on), add `--cap x0,y0,x1,y1`.
3. **Mega entries** (`form: "mega"`): share the base number (e.g. 003 Mega), and the *page* background
   (never the Pokémon image background) shows tiny pale stars/sparkles fading in and out.
4. **Gigantamax entries** (`form: "gmax"`): same idea, but the tiny stars are red-pink.
   Both are driven by the `form` field; the stars live in `#sky` in `index.html`.
5. **Page colour follows the primary type.** Each entry page takes its background tint, image glow and
   accent colour from the Pokémon's primary type (grass = green, fire = orange, ...), using
   `TYPE_COLORS` in `index.html` (sampled from the owner's type-colour reference sheet). The secondary
   type colours the smaller corner glow.
6. **Home page hover theme.** Hovering (or focusing) a card on the home page glows its border in the
   primary-type colour *and* re-themes the whole home page background to that type; leaving the card
   returns to the default green. On touch screens (no hover) the card nearest the middle of the
   screen is treated as hovered while scrolling.
7. **Home card numbers match the type.** The `#004`-style number on each home card is coloured by that
   Pokémon's primary type, not the default green.
8. **Home page: fixed top, scrolling entries.** Everything from the "Living Pokédex" header down to the
   search box stays in place; only the grid of entries scrolls (inside `#scroller`).

Also: add the entry to `POKEDEX` in `index.html`, check home grid + paging, republish the artifact.

## Where things live

- This repository (`marcgoveiawork-bit/living-pokedex`, branch `main`) is the source of truth. After each
  entry or change: commit, push to `main`, and republish the claude.ai artifact from these files.
- Artifact: https://claude.ai/artifact/S1xdSPkv6sanjTmx9jBgds (slug `ca96bfa5-85a2-4764-bc38-9e9fb325bfc6`).
- Phone tilt only works on the GitHub Pages address; the claude.ai viewer blocks motion sensors.

