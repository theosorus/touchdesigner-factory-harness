# The surface cloud: what was done, and how to redo it

> **You do not need Blender for this project.** This document started as a Blender tutorial.
> It turned out to be unnecessary: the brain's surface mesh was already on the machine, and the
> conversion is automated. The Blender route is kept at the end, for the day you change models.

## The problem

The original file, `assets/cloud_brain.ply`, was a **solid** cloud: 262,254 points spread
through the whole thickness of the brain, with no normals. Rendered as points, you saw straight
through it at all times, the silhouette became a mass, and no lighting was possible without
normals.

Worse, under rotation a transparent volume is genuinely ambiguous: front and back points move
in opposite directions on screen, and nothing says which is which. That is **kinetic depth
ambiguity**, the Necker cube family — not the wagon-wheel effect, which needs temporal aliasing
of a periodic pattern and does not apply here.

## What was done instead

`brain.glb` (13 MB, a Sketchfab model derived from an STL) holds the **surface mesh**: 4
objects, 215,601 vertices, 377,701 triangles, **with their normals**. TouchDesigner does not
read glTF, so a small converter turns it into a `.ply`:

```bash
python3 scripts/glb_to_ply.py --no-color --no-faces \
    ~/Downloads/brain.glb \
    assets/brain_surface.ply
```

The script (stdlib only, 0.6 s) does the following:

- reads the `.glb`'s JSON and binary chunks;
- applies the scene transforms, including the rotation matrix Sketchfab puts at the root, which
  yields Y-up directly: **no rotation is needed in TD any more**;
- merges the 4 objects, offsetting the indices;
- recenters on the origin and scales so the largest axis has a half-extent of 1.2, exactly the
  scale of the previous cloud, so every TD setting stayed valid;
- writes a binary `.ply` with positions and normals.

Two flags matter:

- `--no-color`: the File In POP always reads `red/green/blue` as an incoming `Color` attribute,
  which collides with a GLSL POP's `Color` output and breaks shader compilation.
- `--no-faces`: the Point File In POP ignores faces and warns when it finds them. Dropping them
  removes the warning and halves the file.

Check the result if you ever reconvert:

```bash
python3 -c "
d = open('projects/brain-eeg-cloud/assets/brain_surface.ply','rb').read(400)
print(d[:d.find(b'end_header')+10].decode())"
```

You should see `element vertex`, then the `nx ny nz` properties.

## On the TouchDesigner side

The `src_cloud` stage is five operators:

`pointfilein_surface` (Point File In POP, `normalfields = nx ny nz`) -> `random_seed`
(Random POP, one seed per point) -> `delete_decimate` (removes points above the Density
threshold) -> `transform_upright` (identity now) -> `out1`

**A route tested and abandoned**: reading the mesh with a File In POP and scattering points with
a Sprinkle POP, which would have made density a live parameter without regenerating a file. In
`Per Primitive` mode the Sprinkle POP cannot place fewer than one point per primitive: with
377,701 triangles it covered only part of the mesh and produced a brain in pieces. The mesh's
own vertices do the job perfectly well.

## What the normals unlocked

In the `fx_pulse` shader:

- **exact back-face removal**: `dot(N, toCamera)` replaces the radial approximation, and points
  facing away are dropped entirely rather than dimmed. Measured: 43.6% of points are drawn, i.e.
  the visible hemisphere. This is what resolves the rotation ambiguity.
- **lighting**: a warm key top-left, a cool fill on the other side, and a Fresnel term on the
  rims. This is what finally makes the convolutions read.
- **violet follows the relief**: it marks the sulci (where the normal turns away from the key)
  while the ridges stay pink. Before, the pink/violet mix followed distance from the centre,
  which meant nothing visually.

---

# Appendix: making a surface cloud from Blender

Keep this if you change brain models and only have a mesh in Blender.

1. **Geometry Nodes** on the mesh: `Distribute Points on Faces` (method `Poisson Disk`,
   `Distance Min` 0.01, raise `Density Max` until you reach 90,000-150,000 points) ->
   `Vector Math` in `Multiply Add` (x0.5 then +0.5, to move the normal from -1..1 into 0..1) ->
   `Store Named Attribute` (domain `Point`, type `Color`, name `Col`, value = the transposed
   **Normal** output) -> `Points to Vertices`.
2. **Object > Convert > Mesh** to freeze it, otherwise the export sees nothing.
3. **File > Export > Stanford PLY**: binary format, `Selected Only`, `Vertex Colors` on in
   `Linear` space, `Vertex Normals` on, `Scale` 1.0. **Do not touch the Forward/Up axes**: the
   whole pipeline is calibrated on the defaults.
4. On the TD side, if the normals travelled through the colours rather than through `nx ny nz`,
   set `colorfields = r g b` on the loader and decode `N = Color.rgb * 2.0 - 1.0` in the shader.
