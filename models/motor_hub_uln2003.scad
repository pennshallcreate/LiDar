// 28BYJ-48 shaft hub (Budget tier) -- see PRINTS.md.
// IMPORTANT: many 28BYJ-48 kits ship with a small plastic coupler/gear
// already pressed onto the output shaft. Either remove it and bore this
// hub for the bare ~5mm D-shaft (default below), or measure that
// coupler's OD and change shaft_bore_d to clamp onto it instead -- check
// your kit before printing. Bolts to the platter via the same 3x M3
// pattern as motor_hub_nema17.scad (must match platter.scad).
// Print with the bore axis vertical, no supports needed.
$fn = 64;

hub_d = 30;
hub_h = 12;   // 28BYJ-48's output shaft is shorter than a NEMA17's -- less engagement needed/available

shaft_bore_d = 5.2;    // verify against your kit -- see note above
setscrew_d = 3.2;

bolt_circle_d = 20;    // MUST match platter.scad's hub_bolt_circle_d
bolt_hole_d = 3.4;
bolt_angles = [90, 210, 330];  // MUST match platter.scad's hub_angles

difference() {
    cylinder(d = hub_d, h = hub_h);

    translate([0, 0, -1]) cylinder(d = shaft_bore_d, h = hub_h + 2);

    translate([0, 0, hub_h / 2])
        rotate([0, 90, 0])
            cylinder(d = setscrew_d, h = hub_d, center = true);

    translate([0, 0, hub_h - 4])
        for (a = bolt_angles)
            rotate([0, 0, a])
                translate([bolt_circle_d / 2, 0, 0])
                    cylinder(d = bolt_hole_d, h = 10);
}
