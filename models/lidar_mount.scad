// LiDAR mount bracket -- see PRINTS.md.
// Bolts flat to the mast's top flange; the vertical wall holds the
// LD06/LD19 with its spin axis HORIZONTAL (mounting face vertical) so the
// beam sweeps a vertical circle -- see ARCHITECTURE.md section 1 for why.
// IMPORTANT: the sensor's bolt-circle diameter below is an approximate,
// commonly-cited figure, NOT measured from a datasheet in hand -- verify
// against your actual unit before finalizing hole positions (PRINTS.md).
// Print with the foot face-down, no supports needed (wall is a
// straight vertical extrusion from the foot's back edge).
$fn = 64;

// Foot: flat, bolts down to the mast's top flange. Centered on X=0,
// spans Y = [-foot_d/2, +foot_d/2], Z = [0, foot_t].
foot_w = 40; foot_d = 30; foot_t = 4;
mast_hole_spacing = 25;   // MUST match mast.scad's lidar_bolt_spacing
mast_hole_d = 3.4;

// Wall: rises from the foot's back edge (Y = +foot_d/2), full height
// measured from the TOP of the foot (Z = foot_t).
wall_h = 45; wall_t = 4;
wall_y0 = foot_d / 2 - wall_t;   // wall's Y-span: [wall_y0, wall_y0 + wall_t]
wall_y_center = wall_y0 + wall_t / 2;
wall_z0 = foot_t;

sensor_bolt_circle_d = 27;  // APPROXIMATE -- verify against your LD06/LD19
sensor_hole_d = 2.5;        // M2/M2.5 -- verify
sensor_angles = [90, 210, 330];
cable_clearance_d = 15;

overlap = 0.5;  // guarantee real overlap between foot and wall, not a coincident face

module foot() {
    difference() {
        translate([-foot_w / 2, -foot_d / 2, 0])
            cube([foot_w, foot_d, foot_t]);

        translate([-mast_hole_spacing / 2, 0, -1]) cylinder(d = mast_hole_d, h = foot_t + 2);
        translate([mast_hole_spacing / 2, 0, -1]) cylinder(d = mast_hole_d, h = foot_t + 2);
    }
}

module wall() {
    difference() {
        translate([-foot_w / 2, wall_y0, wall_z0 - overlap])
            cube([foot_w, wall_t, wall_h + overlap]);

        // sensor bolt circle + cable clearance, drilled straight through
        // the wall's thickness (along Y), centered on the wall's face
        translate([0, wall_y_center, wall_z0 + wall_h / 2])
            rotate([90, 0, 0]) {
                cylinder(d = cable_clearance_d, h = wall_t + 20, center = true);
                for (a = sensor_angles)
                    rotate([0, 0, a])
                        translate([sensor_bolt_circle_d / 2, 0, 0])
                            cylinder(d = sensor_hole_d, h = wall_t + 20, center = true);
            }
    }
}

union() {
    foot();
    wall();
}
