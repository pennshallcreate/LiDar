"""
Point-cloud assembly and PLY export -- pure NumPy, no Open3D dependency
(see ARCHITECTURE.md section 2 for why that's a deliberate choice for a
512 MB Pi Zero 2 W).

The 2D->3D merge transform pipeline (translate by the sensor's offset from
the rotation axis, rotate by a fixed mechanical mounting-angle correction,
then revolve by each revolution's recorded turntable azimuth) mirrors
PiLiDAR's lib/pointcloud.py (https://github.com/PiLiDAR/PiLiDAR),
(c) Philip Gutjahr, CC BY-NC-SA 4.0, reimplemented here with plain
rotation matrices instead of Open3D geometry calls.
"""

import os
import pickle

import numpy as np


# ----------------------------------------------------------------------------
# raw scan (per-revolution 2D data) persistence

def get_scan_dict(z_angles, cartesian_list, scan_id=None):
    return {"header": {"scan_id": scan_id}, "z_angles": z_angles, "cartesian": cartesian_list}


def save_raw_scan(path, data):
    with open(path, "wb") as f:
        pickle.dump(data, f)


def load_raw_scan(path):
    with open(path, "rb") as f:
        return pickle.load(f)


# ----------------------------------------------------------------------------
# 2D -> 3D merge

def _rotation_matrix(axis, radians):
    c, s = np.cos(radians), np.sin(radians)
    if axis == "x":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    if axis == "z":
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    raise ValueError(f"axis must be 'x', 'y' or 'z', got {axis!r}")


def merge_2D_points(raw_scan, position_offset=(0.0, 0.0, 0.0), angle_offset=0.0):
    """Revolve every recorded LiDAR revolution (a 2D vertical-plane slice)
    around the turntable axis by its recorded azimuth angle, producing one
    merged (N, 4) XYZI point cloud.

    position_offset: (x, y, z) mm translation applied before the azimuth
        revolve -- corrects for the LiDAR not sitting exactly on the
        rotation axis (mechanical offset of the mast/bracket).
    angle_offset: degrees, rotation around the vertical mast's own tilt
        axis -- corrects small mounting-angle error. Tune both via the
        procedure in BUILD.md's calibration checklist.
    """
    z_angles = raw_scan["z_angles"]
    cartesian_list = raw_scan["cartesian"]

    offset_rotation = _rotation_matrix("y", np.radians(angle_offset))
    translation = np.asarray(position_offset, dtype=np.float64)

    chunks = []
    for points_2d, z_angle in zip(cartesian_list, z_angles):
        if z_angle is None or points_2d is None or len(points_2d) == 0:
            continue

        n = points_2d.shape[0]
        xyz = np.zeros((n, 3), dtype=np.float64)
        xyz[:, 0] = points_2d[:, 0]   # local (radial) x -> world X
        xyz[:, 2] = points_2d[:, 1]   # local (vertical) y -> world Z
        intensity = points_2d[:, 2]

        xyz += translation
        xyz = xyz @ offset_rotation.T

        revolve = _rotation_matrix("z", np.radians(-z_angle))
        xyz = xyz @ revolve.T

        chunks.append(np.column_stack((xyz, intensity)))

    if not chunks:
        return np.empty((0, 4), dtype=np.float64)

    points = np.concatenate(chunks, axis=0)
    return points[~np.isnan(points).any(axis=1)]


# ----------------------------------------------------------------------------
# intensity -> color (no matplotlib dependency)

_GRADIENT_STOPS = np.array([
    [0.05, 0.05, 0.30],   # dark blue  (low intensity / far or dark surfaces)
    [0.00, 0.80, 0.80],   # cyan
    [0.95, 0.90, 0.10],   # yellow
    [0.80, 0.05, 0.05],   # red        (high intensity / close or bright surfaces)
])


def intensity_to_rgb(intensity, mode="gradient"):
    """intensity: 1D array (raw LD06/LD19 luminance byte, 0-255).
    Returns (N, 3) uint8 RGB. mode='gray' repeats normalized intensity
    across R=G=B; mode='gradient' (default) maps it through a small
    dark-blue -> cyan -> yellow -> red heatmap for a more readable
    visualization in MeshLab/CloudCompare."""
    i = np.asarray(intensity, dtype=np.float64)
    if i.size == 0:
        return np.empty((0, 3), dtype=np.uint8)

    lo, hi = np.percentile(i, 1), np.percentile(i, 99)
    if hi <= lo:
        hi = lo + 1.0
    t = np.clip((i - lo) / (hi - lo), 0.0, 1.0)

    if mode == "gray":
        g = (t * 255).astype(np.uint8)
        return np.column_stack((g, g, g))

    n_segs = len(_GRADIENT_STOPS) - 1
    seg = np.clip((t * n_segs).astype(int), 0, n_segs - 1)
    local_t = (t * n_segs) - seg
    c0 = _GRADIENT_STOPS[seg]
    c1 = _GRADIENT_STOPS[seg + 1]
    rgb = c0 + (c1 - c0) * local_t[:, None]
    return np.clip(rgb * 255, 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------------
# PLY export

def save_ply(filepath, points_xyz, colors_rgb=None, ascii_mode=False):
    """Write a point cloud to a .ply file (binary_little_endian by
    default). points_xyz: (N, 3) float array. colors_rgb: optional
    (N, 3) uint8 array; omit for an uncolored cloud."""
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)

    points_xyz = np.asarray(points_xyz, dtype=np.float64)
    n = points_xyz.shape[0]
    has_color = colors_rgb is not None

    header_lines = [
        "ply",
        f"format {'ascii' if ascii_mode else 'binary_little_endian'} 1.0",
        "comment generated by DIY LiDAR scanner (github.com/pennshallcreate/LiDar)",
        f"element vertex {n}",
        "property float x", "property float y", "property float z",
    ]
    if has_color:
        header_lines += ["property uchar red", "property uchar green", "property uchar blue"]
    header_lines.append("end_header")
    header = ("\n".join(header_lines) + "\n").encode("ascii")

    if ascii_mode:
        lines = []
        if has_color:
            for (x, y, z), (r, g, b) in zip(points_xyz, colors_rgb):
                lines.append(f"{x:.4f} {y:.4f} {z:.4f} {int(r)} {int(g)} {int(b)}")
        else:
            for x, y, z in points_xyz:
                lines.append(f"{x:.4f} {y:.4f} {z:.4f}")
        with open(filepath, "wb") as f:
            f.write(header)
            f.write(("\n".join(lines) + ("\n" if lines else "")).encode("ascii"))
        return

    if has_color:
        colors_rgb = np.asarray(colors_rgb, dtype=np.uint8)
        record = np.zeros(n, dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4"),
                                     ("red", "u1"), ("green", "u1"), ("blue", "u1")])
        record["red"], record["green"], record["blue"] = colors_rgb[:, 0], colors_rgb[:, 1], colors_rgb[:, 2]
    else:
        record = np.zeros(n, dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4")])

    record["x"], record["y"], record["z"] = points_xyz[:, 0], points_xyz[:, 1], points_xyz[:, 2]

    with open(filepath, "wb") as f:
        f.write(header)
        f.write(record.tobytes())


if __name__ == "__main__":
    # synthetic self-test: a single "revolution" that's a vertical line of
    # points, revolved through 4 azimuth steps -> should produce a
    # 4-spoke cross pattern when viewed from above.
    fake_line = np.column_stack((
        np.full(5, 1000.0),         # local x (radial distance, mm)
        np.linspace(-500, 500, 5),  # local y (vertical extent, mm)
        np.linspace(0, 255, 5),     # intensity
    )).astype(np.float32)

    raw = get_scan_dict(
        z_angles=[0, 90, 180, 270],
        cartesian_list=[fake_line, fake_line, fake_line, fake_line],
        scan_id="selftest",
    )
    pts = merge_2D_points(raw)
    assert pts.shape == (20, 4), f"expected 20 points, got {pts.shape}"
    colors = intensity_to_rgb(pts[:, 3])
    out_path = "/tmp/pointcloud_selftest.ply"
    save_ply(out_path, pts[:, :3], colors)
    print(f"self-test OK: wrote {pts.shape[0]} points to {out_path}")
