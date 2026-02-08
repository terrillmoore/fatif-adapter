// Fatif DS 20x25 Adapter Lensboard
// Accepts 138.5mm Gowland 8x10 lensboards via horizontal slide
// 
// Design: Terry Moore / Claude
// Date: 2026-02-07
// Material: 6061-T6 aluminum, machined from 6mm stock
// All dimensions in mm
//
// Orientation:
//   Back face (camera side) at z=0
//   Front face (lens side) at z=5.5
//   Board slides in from +X direction
//   Fixed stop on -X side
//   Ball plunger on -Y side wall

$fn = 120;  // smooth curves for rendering

// === PARAMETERS ===

// Outer board profile
board_size = 170;           // overall square dimension
board_corner_r = 50;        // corner radius
board_thickness = 5.5;      // total thickness (face 6mm stock to this)

// Back perimeter step (seats into Fatif front standard)
step_width = 7.5;           // width of step from outer edge
step_depth = 3.0;           // depth milled from back face
// Inner profile of step:
step_inner_size = board_size - 2*step_width;  // 155mm
step_inner_r = board_corner_r - step_width;   // 42.5mm

// Front recess for Gowland board
gowland_size = 139.0;      // 138.5 nominal + 0.5mm clearance
gowland_corner_r = 3.4;    // corner radius of Gowland boards
recess_depth = 0.5;         // depth of recess from front face

// Through hole
bore_dia = 110;             // diameter of central bore

// Ball plunger (M6 x 1.0 thread, typical)
// Located in -Y wall of recess, centered on slide axis
plunger_thread_dia = 6.0;   // M6
plunger_depth = 10.0;       // depth of tapped hole
// Position: centered on X axis, in the -Y wall of the recess
plunger_y = -gowland_size/2;
plunger_z = board_thickness - recess_depth/2;  // centered in recess wall height

// Slide opening extension
// The recess extends to the outer profile on the +X side
slide_opening_extension = (board_size - gowland_size)/2 + 5; // extend past board edge

// === MODULES ===

module rounded_rect_2d(w, h, r) {
    hull() {
        translate([ w/2-r,  h/2-r]) circle(r=r);
        translate([-w/2+r,  h/2-r]) circle(r=r);
        translate([-w/2+r, -h/2+r]) circle(r=r);
        translate([ w/2-r, -h/2+r]) circle(r=r);
    }
}

module rounded_rect(w, h, r, height) {
    linear_extrude(height)
    rounded_rect_2d(w, h, r);
}

// === MAIN BODY ===

difference() {
    // 1. Start with full-thickness board
    rounded_rect(board_size, board_size, board_corner_r, board_thickness);

    // 2. Back perimeter step: remove 3mm from back face in the outer ring
    //    We subtract the inner (raised) area from a full-depth cut of the outer area
    translate([0, 0, -0.01])
    difference() {
        rounded_rect(board_size + 1, board_size + 1, board_corner_r, step_depth + 0.01);
        translate([0, 0, -0.1])
        rounded_rect(step_inner_size, step_inner_size, step_inner_r, step_depth + 0.2);
    }

    // 3. Front recess for Gowland board
    //    Pocket is 0.5mm deep from front face
    //    Open on +X side for slide entry
    translate([0, 0, board_thickness - recess_depth])
    union() {
        // Main recess pocket
        linear_extrude(recess_depth + 0.01)
        rounded_rect_2d(gowland_size, gowland_size, gowland_corner_r);

        // Slide opening: extend recess to +X edge of board
        // This is a rectangular extension from the recess to the board edge
        translate([gowland_size/4, 0, 0])
        linear_extrude(recess_depth + 0.01)
        square([gowland_size/2 + slide_opening_extension, gowland_size], center=true);
    }

    // 4. Central through-bore
    translate([0, 0, -0.01])
    cylinder(d=bore_dia, h=board_thickness + 0.02);

    // 5. Ball plunger tapped hole (M6)
    //    In the -Y wall of the recess, horizontal, pointing +Y
    //    Positioned at X=0 (centered on slide axis)
    translate([0, plunger_y - 0.01, plunger_z])
    rotate([-90, 0, 0])
    cylinder(d=plunger_thread_dia, h=plunger_depth);
}

// === ANNOTATIONS (for reference, disable for export) ===
// Uncomment to see Gowland board ghost:
// %translate([0, 0, board_thickness - recess_depth])
//   color("blue", 0.3)
//   rounded_rect(138.5, 138.5, 3.4, 1.6);
