// Base plate -- see PRINTS.md for the full dimensioned spec.
// Print flat, no supports needed. PETG or PLA, 3-4 walls, 25% infill.
$fn = 64;

// ---- key parameters (edit to match YOUR parts before printing) ----------
plate_x = 220;
plate_y = 150;
plate_t = 4;
corner_r = 8;

bearing_center = [70, 75];       // rotation axis -- also motor + platter center
bearing_bolt_circle_d = 85;      // verify against your actual bearing, see PRINTS.md
bearing_slot_w = 4;
bearing_slot_l = 12;
center_bore_d = 30;              // motor shaft + wiring pass-through

nema17_pattern = 31.04;          // standard NEMA17 mounting square
uln2003_spacing = 35;            // 28BYJ-48 ear-to-ear spacing (verify against your unit)
motor_hole_d = 3.4;              // M3 clearance

tripod_center = [110, 75];
tripod_boss_d = 20;
tripod_pilot_d = 9.6;            // standard 1/4"-20 heat-set insert pilot -- verify against yours
tripod_boss_h = 10;

foot_positions = [[15, 15], [15, 135], [205, 15], [205, 135]];  // 4 corners, clear of the grid (see clearance note in PRINTS.md)
foot_d = 14;
foot_h = 40;                     // clears the NEMA17 body hanging underneath

button_holes = [[150, 8], [180, 8]];  // 8mm margin from edge -- was 0 (on the edge), which cut open notches instead of round holes
button_d = 12;

// electronics mounting grid (generic -- fits Pi/driver/boost/terminal block
// regardless of exact layout, see PRINTS.md rationale)
grid_x0 = 135; grid_x1 = 190;
grid_y0 = 35;  grid_y1 = 115;  // kept well clear (>=20mm) of feet/buttons/straps/edges -- see PRINTS.md clearance note
grid_step = 20;
grid_hole_d = 3.4;

// battery-strap slots (power bank is strapped on, not enclosed -- see PRINTS.md)
strap_slots = [[130, 8], [130, 142]];
strap_slot_w = 20;
strap_slot_h = 3;

// ---------------------------------------------------------------------

module rounded_rect(x, y, r) {
    hull() {
        for (dx = [r, x - r])
            for (dy = [r, y - r])
                translate([dx, dy]) circle(r = r);
    }
}

module bearing_slots(center, bolt_circle_d, slot_w, slot_l) {
    for (a = [45, 135, 225, 315])
        translate(center)
            rotate([0, 0, a])
                translate([bolt_circle_d / 2, 0])
                    square([slot_l, slot_w], center = true);
}

module nema17_holes(center, pattern, hole_d) {
    for (dx = [-pattern / 2, pattern / 2])
        for (dy = [-pattern / 2, pattern / 2])
            translate(center + [dx, dy])
                circle(d = hole_d);
}

module uln2003_holes(center, spacing, hole_d) {
    for (dx = [-spacing / 2, spacing / 2])
        translate(center + [dx, 0])
            circle(d = hole_d);
}

module mounting_grid(x0, x1, y0, y1, step, hole_d) {
    nx = floor((x1 - x0) / step);
    ny = floor((y1 - y0) / step);
    for (i = [0:nx])
        for (j = [0:ny])
            translate([x0 + i * step, y0 + j * step])
                circle(d = hole_d);
}

module base_plate_2d() {
    difference() {
        rounded_rect(plate_x, plate_y, corner_r);

        translate(bearing_center) circle(d = center_bore_d);
        bearing_slots(bearing_center, bearing_bolt_circle_d, bearing_slot_w, bearing_slot_l);
        nema17_holes(bearing_center, nema17_pattern, motor_hole_d);
        uln2003_holes(bearing_center, uln2003_spacing, motor_hole_d);

        mounting_grid(grid_x0, grid_x1, grid_y0, grid_y1, grid_step, grid_hole_d);

        for (p = button_holes) translate(p) circle(d = button_d);
        for (p = strap_slots) translate(p) square([strap_slot_w, strap_slot_h], center = true);
    }
}

module tripod_boss() {
    overlap = 0.5; // ensure a real overlap with the plate, not a coincident face
    translate([tripod_center[0], tripod_center[1], -tripod_boss_h])
        difference() {
            cylinder(d = tripod_boss_d, h = tripod_boss_h + overlap);
            translate([0, 0, -1]) cylinder(d = tripod_pilot_d, h = tripod_boss_h + 2 + overlap);
        }
}

module feet() {
    overlap = 0.5; // ditto
    for (p = foot_positions)
        translate([p[0], p[1], -foot_h])
            cylinder(d = foot_d, h = foot_h + overlap);
}

union() {
    linear_extrude(height = plate_t) base_plate_2d();
    tripod_boss();
    feet();
}
