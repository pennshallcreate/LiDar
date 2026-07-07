// NEMA17 shaft hub (Recommended tier) -- see PRINTS.md.
// Clamps onto the NEMA17's 5mm D-shaft via a radial M3 set screw, bolts
// to the platter's underside via 3x M3 on the hub_bolt_circle_d pattern
// (must match platter.scad). Print with the bore axis vertical, no
// supports needed. PETG recommended -- this part sees the most stress
// in the whole build (all drive torque passes through it).
$fn = 64;

hub_d = 30;   // bumped from 25 -- with a 20mm bolt circle + 3.4mm holes, 25 left only ~0.8mm wall at the hub edge
hub_h = 15;

shaft_bore_d = 5.2;    // NEMA17 shaft is 5mm nominal -- +0.2mm print fit allowance
setscrew_d = 3.2;      // M3 set screw, thread-formed directly into the print
                       // (or tap M3 / use a threaded insert)

bolt_circle_d = 20;    // MUST match platter.scad's hub_bolt_circle_d
bolt_hole_d = 3.4;
bolt_angles = [90, 210, 330];  // MUST match platter.scad's hub_angles

difference() {
    cylinder(d = hub_d, h = hub_h);

    translate([0, 0, -1]) cylinder(d = shaft_bore_d, h = hub_h + 2);

    // radial set screw, midway up the bore
    translate([0, 0, hub_h / 2])
        rotate([0, 90, 0])
            cylinder(d = setscrew_d, h = hub_d, center = true);

    translate([0, 0, hub_h - 4])
        for (a = bolt_angles)
            rotate([0, 0, a])
                translate([bolt_circle_d / 2, 0, 0])
                    cylinder(d = bolt_hole_d, h = 10);
}
