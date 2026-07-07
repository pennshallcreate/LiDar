// Mast (vertical column) -- see PRINTS.md. Connects the platter to the
// LiDAR mount bracket. Solid post (not hollow) for print simplicity and
// rigidity; route the LiDAR's 4 wires externally, zip-tied to the mast
// (see BUILD.md) rather than through an internal channel.
// Print standing up, no supports needed for the post itself; the flanges'
// undersides may want a brim. PETG recommended (PLA can creep/lean
// slightly over time under the sensor's small offset load).
$fn = 64;

post_w = 20;         // square post cross-section
post_h = 160;        // platter-top to lidar-mount-face height -- see
                      // ARCHITECTURE.md for why this clearance matters

bottom_flange_d = 70;
bottom_flange_t = 4;
mast_bolt_circle_d = 60;   // MUST match platter.scad's mast_bolt_circle_d
mast_hole_d = 3.4;
mast_angles = [0, 90, 180, 270];

top_flange_d = 40;
top_flange_t = 4;
lidar_bolt_spacing = 25;   // 2-hole pattern, see lidar_mount.scad
lidar_hole_d = 3.4;

module bolt_circle_holes(bolt_circle_d, hole_d, angles) {
    for (a = angles)
        rotate([0, 0, a])
            translate([bolt_circle_d / 2, 0])
                circle(d = hole_d);
}

module bottom_flange() {
    difference() {
        cylinder(d = bottom_flange_d, h = bottom_flange_t);
        translate([0, 0, -1])
            linear_extrude(bottom_flange_t + 2)
                bolt_circle_holes(mast_bolt_circle_d, mast_hole_d, mast_angles);
    }
}

module top_flange() {
    translate([0, 0, post_h])
        difference() {
            cylinder(d = top_flange_d, h = top_flange_t);
            translate([-lidar_bolt_spacing / 2, 0, -1]) cylinder(d = lidar_hole_d, h = top_flange_t + 2);
            translate([lidar_bolt_spacing / 2, 0, -1]) cylinder(d = lidar_hole_d, h = top_flange_t + 2);
        }
}

union() {
    bottom_flange();
    translate([-post_w / 2, -post_w / 2, -0.5]) cube([post_w, post_w, post_h + 0.5]);
    top_flange();
}
