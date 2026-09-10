#!/usr/bin/env python3
"""Convert a .glb (binary glTF 2.0) into a binary .ply the File In POP can read.

TouchDesigner's File In POP does not read glTF. This script extracts the meshes from
a .glb, applies the scene transforms, merges everything, recenters and scales it, then
writes a binary .ply with positions, normals, per-vertex colours and triangle faces.

Usage:
    python3 scripts/glb_to_ply.py <input.glb> <output.ply> [--half-extent 1.2]

Dependencies: stdlib only.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from array import array
from pathlib import Path

# glTF componentType -> (struct format, size in bytes)
COMPONENT = {
    5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2),
    5123: ('H', 2), 5125: ('I', 4), 5126: ('f', 4),
}
NUM_COMPS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read_glb(path: Path) -> tuple[dict, bytes]:
    """Return the scene JSON and the binary buffer."""
    data = path.read_bytes()
    magic, version, _ = struct.unpack_from('<4sII', data, 0)
    if magic != b'glTF':
        raise ValueError(f'{path} is not a glb (magic {magic!r})')
    if version != 2:
        raise ValueError(f'unsupported glTF version {version}')
    offset, gltf, buf = 12, None, b''
    while offset < len(data):
        clen, ctype = struct.unpack_from('<I4s', data, offset)
        chunk = data[offset + 8:offset + 8 + clen]
        if ctype == b'JSON':
            gltf = json.loads(chunk.decode('utf-8'))
        elif ctype == b'BIN\x00':
            buf = chunk
        offset += 8 + clen + (-clen % 4)
    if gltf is None:
        raise ValueError('no JSON chunk in the glb')
    return gltf, buf


def read_accessor(gltf: dict, buf: bytes, index: int) -> list:
    """Read an accessor and return a flat list of values."""
    acc = gltf['accessors'][index]
    fmt, size = COMPONENT[acc['componentType']]
    ncomp = NUM_COMPS[acc['type']]
    count = acc['count']
    view = gltf['bufferViews'][acc['bufferView']]
    start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    stride = view.get('byteStride') or (size * ncomp)

    if stride == size * ncomp:                      # tightly packed
        raw = buf[start:start + count * ncomp * size]
        out = array(fmt)
        out.frombytes(raw)
        if sys.byteorder != 'little':
            out.byteswap()
        return list(out)

    out = []                                        # interleaved
    unpack = struct.Struct('<' + fmt * ncomp).unpack_from
    for i in range(count):
        out.extend(unpack(buf, start + i * stride))
    return out


def node_matrix(node: dict) -> list[float]:
    """The node's column-major 4x4 matrix, identity by default."""
    if 'matrix' in node:
        return list(node['matrix'])
    m = [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0]
    t = node.get('translation')
    s = node.get('scale')
    r = node.get('rotation')
    if r:                                           # quaternion x, y, z, w
        x, y, z, w = r
        m = [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w), 0,
             2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w), 0,
             2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y), 0,
             0, 0, 0, 1]
    if s:
        for c in range(3):
            for row in range(3):
                m[c * 4 + row] *= s[c]
    if t:
        m[12], m[13], m[14] = t
    return m


def mat_mul(a: list[float], b: list[float]) -> list[float]:
    """a * b, column-major 4x4 matrices."""
    out = [0.0] * 16
    for c in range(4):
        for r in range(4):
            out[c * 4 + r] = sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4))
    return out


def collect(gltf: dict, buf: bytes) -> tuple[list, list, list, list]:
    """Walk the scene and return positions, normals, colours and triangles."""
    positions: list[float] = []
    normals: list[float] = []
    colors: list[float] = []
    tris: list[int] = []
    scene = gltf['scenes'][gltf.get('scene', 0)]

    def walk(node_index: int, parent: list[float]) -> None:
        node = gltf['nodes'][node_index]
        world = mat_mul(parent, node_matrix(node))
        if 'mesh' in node:
            for prim in gltf['meshes'][node['mesh']].get('primitives', []):
                if prim.get('mode', 4) != 4:        # triangles only
                    continue
                attrs = prim['attributes']
                base = len(positions) // 3
                pos = read_accessor(gltf, buf, attrs['POSITION'])
                nrm = read_accessor(gltf, buf, attrs['NORMAL']) if 'NORMAL' in attrs else None
                col = read_accessor(gltf, buf, attrs['COLOR_0']) if 'COLOR_0' in attrs else None
                ncol = NUM_COMPS[gltf['accessors'][attrs['COLOR_0']]['type']] if col else 0

                for i in range(len(pos) // 3):
                    x, y, z = pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]
                    positions.extend((
                        world[0] * x + world[4] * y + world[8] * z + world[12],
                        world[1] * x + world[5] * y + world[9] * z + world[13],
                        world[2] * x + world[6] * y + world[10] * z + world[14]))
                    if nrm:                          # rotation only, no translation
                        nx, ny, nz = nrm[3 * i], nrm[3 * i + 1], nrm[3 * i + 2]
                        vx = world[0] * nx + world[4] * ny + world[8] * nz
                        vy = world[1] * nx + world[5] * ny + world[9] * nz
                        vz = world[2] * nx + world[6] * ny + world[10] * nz
                        length = (vx * vx + vy * vy + vz * vz) ** 0.5 or 1.0
                        normals.extend((vx / length, vy / length, vz / length))
                    else:
                        normals.extend((0.0, 0.0, 1.0))
                    if col:
                        colors.extend(col[ncol * i:ncol * i + 3])
                    else:
                        colors.extend((1.0, 1.0, 1.0))

                idx = read_accessor(gltf, buf, prim['indices'])
                tris.extend(v + base for v in idx)
        for child in node.get('children', []):
            walk(child, world)

    identity = [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0]
    for root in scene['nodes']:
        walk(root, identity)
    return positions, normals, colors, tris


def normalize(positions: list[float], half_extent: float) -> tuple[float, list[float]]:
    """Recenter on the origin and scale. Returns (factor, center)."""
    lo = [min(positions[i::3]) for i in range(3)]
    hi = [max(positions[i::3]) for i in range(3)]
    center = [(lo[i] + hi[i]) / 2.0 for i in range(3)]
    largest = max((hi[i] - lo[i]) / 2.0 for i in range(3)) or 1.0
    factor = half_extent / largest
    for i in range(0, len(positions), 3):
        positions[i] = (positions[i] - center[0]) * factor
        positions[i + 1] = (positions[i + 1] - center[1]) * factor
        positions[i + 2] = (positions[i + 2] - center[2]) * factor
    return factor, center


def write_ply(path: Path, positions, normals, colors, tris, with_color: bool = True,
              with_faces: bool = True) -> None:
    nverts = len(positions) // 3
    nfaces = len(tris) // 3 if with_faces else 0
    header = (
        'ply\n'
        'format binary_little_endian 1.0\n'
        'comment converted from glTF by scripts/glb_to_ply.py\n'
        f'element vertex {nverts}\n'
        'property float x\nproperty float y\nproperty float z\n'
        'property float nx\nproperty float ny\nproperty float nz\n'
        + ('property uchar red\nproperty uchar green\nproperty uchar blue\n' if with_color else '')
        + (f'element face {nfaces}\nproperty list uchar uint vertex_indices\n' if with_faces else '')
        + 'end_header\n'
    ).encode('ascii')

    vertex = struct.Struct('<6f3B' if with_color else '<6f')
    body = bytearray()
    for i in range(nverts):
        row = (positions[3 * i], positions[3 * i + 1], positions[3 * i + 2],
               normals[3 * i], normals[3 * i + 1], normals[3 * i + 2])
        if with_color:
            row += (max(0, min(255, int(colors[3 * i] * 255))),
                    max(0, min(255, int(colors[3 * i + 1] * 255))),
                    max(0, min(255, int(colors[3 * i + 2] * 255))))
        body += vertex.pack(*row)
    if with_faces:
        face = struct.Struct('<B3I')
        for i in range(nfaces):
            body += face.pack(3, tris[3 * i], tris[3 * i + 1], tris[3 * i + 2])
    path.write_bytes(header + bytes(body))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('source')
    ap.add_argument('dest')
    ap.add_argument('--no-color', action='store_true',
                    help="do not write per-vertex colours. Use it when the downstream produces "
                         "its own colour: the File In POP always reads red/green/blue as a "
                         "Color attribute, which collides with a GLSL POP Color output.")
    ap.add_argument('--no-faces', action='store_true',
                    help="write vertices only. The Point File In POP ignores faces and warns "
                         "when it finds them: this removes the warning and halves the file.")
    ap.add_argument('--half-extent', type=float, default=1.2,
                    help='target half-extent of the largest axis (default 1.2, the scale the '
                         'project is calibrated on)')
    args = ap.parse_args()

    gltf, buf = read_glb(Path(args.source))
    positions, normals, colors, tris = collect(gltf, buf)
    if not positions:
        print('no triangles found', file=sys.stderr)
        return 1
    factor, center = normalize(positions, args.half_extent)
    write_ply(Path(args.dest), positions, normals, colors, tris, with_color=not args.no_color,
              with_faces=not args.no_faces)

    lo = [round(min(positions[i::3]), 3) for i in range(3)]
    hi = [round(max(positions[i::3]), 3) for i in range(3)]
    print(f'vertices  : {len(positions) // 3}')
    print(f'triangles : {len(tris) // 3}')
    print(f'scale     : x{factor:.5f}, original center {[round(c, 2) for c in center]}')
    print(f'bounds    : min {lo}  max {hi}')
    print(f'written   : {args.dest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
