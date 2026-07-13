// Rotating platter (turntable top) -- see PRINTS.md.
// Print flat, no supports. PETG or PLA, 4+ walls, 30-40% infill (carries
// the mast + LiDAR, print it a bit denser than the base plate).
$fn = 64;

disc_d = 120;
disc_t = 4;

bearing_bolt_circle_d = 85;      // MUST match base_plate.scad -- same bearing, top leaf
bearing_slot_w = 4;
bearing_slot_l = 12;
bearing_slot_angles = [45, 135, 225, 315];

hub_bolt_circle_d = 20;          // motor hub attachment (see motor_hub_*.scad)
hub_hole_d = 3.4;
hub_angles = [90, 210, 330];      // 3-bolt pattern

mast_bolt_circle_d = 60;         // offset both in radius and angle from the
mast_hole_d = 3.4;               // bearing slots so nothing overlaps -- see
mast_angles = [0, 90, 180, 270]; // PRINTS.md clearance note

module bolt_circle_holes(bolt_circle_d, hole_d, angles) {
    for (a = angles)
        rotate([0, 0, a])
            translate([bolt_circle_d / 2, 0])
                circle(d = hole_d);
}

module bearing_slots() {
    for (a = bearing_slot_angles)
        rotate([0, 0, a])
            translate([bearing_bolt_circle_d / 2, 0])
                square([bearing_slot_l, bearing_slot_w], center = true);
}

difference() {
    cylinder(d = disc_d, h = disc_t);

    translate([0, 0, -1]) linear_extrude(disc_t + 2) {
        bearing_slots();
        bolt_circle_holes(hub_bolt_circle_d, hub_hole_d, hub_angles);
        bolt_circle_holes(mast_bolt_circle_d, mast_hole_d, mast_angles);
    }
}
