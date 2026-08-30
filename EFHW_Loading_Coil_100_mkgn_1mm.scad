$fn = $preview ? 64 : 160;

/* [Coil] */
L_uH = 100;
winding_d = 55;
wire_cu_d = 1.0;
wire_od = 0; // 0 = авто ПЭТВ-2

/* [Former] */
wall = 2;
flange_len = 14.5;
flange_over_wire = 0.5;
m4_d = 4.5;

/* [Preview] */
show_winding = false;
show_shrink = false;
shrink_wall = 0.6;

function in_from_mm(mm) = mm / 25.4;

function petv2_od(cu_d) = cu_d + 0.093;

function wire_od_eff(cu_d, od) = od <= 0 ? petv2_od(cu_d) : od;

function wheeler_n(L, r_mm, pitch_mm) =
    let (
        r = in_from_mm(r_mm),
        p = in_from_mm(pitch_mm),
        disc = pow(10 * L * p, 2) + 36 * L * pow(r, 3)
    )
    (10 * L * p + sqrt(disc)) / (2 * r * r);

function wheeler_L(N, r_mm, pitch_mm) =
    let (
        r = in_from_mm(r_mm),
        ell = in_from_mm(N * pitch_mm)
    )
    r * r * N * N / (9 * r + 10 * ell);

od = wire_od_eff(wire_cu_d, wire_od);
inner_d = winding_d - 2 * wall;
pitch = od;
r_mm = (winding_d + od) / 2;
N_exact = wheeler_n(L_uH, r_mm, pitch);
N_finite = N_exact == N_exact && N_exact > 0 && N_exact < 1e6;
N = N_finite ? max(1, round(N_exact)) : 0;
winding_len = N * pitch;
length = winding_len + 2 * flange_len;
flange_od = winding_d + 2 * (od + flange_over_wire);
lead_d = 2 * od;
L_actual = N_finite ? wheeler_L(N, r_mm, pitch) : 0;
use_mid_leads = (winding_len - 2 * lead_d - 2) < lead_d;
geometry_ok = inner_d > 0 && N_finite && winding_len > 0;

function lead_z(sign) =
    use_mid_leads
        ? sign * winding_len / 4
        : sign * (winding_len / 2 - lead_d / 2 - 1);

module radial_cut(d, z) {
    translate([0, 0, z])
        rotate([90, 0, 0])
            cylinder(h = flange_od / 2 + 5, d = d, center = false);
}

module former() {
    difference() {
        union() {
            difference() {
                cylinder(h = length, d = winding_d, center = true);
                cylinder(h = length + 2, d = inner_d, center = true);
            }
            for (z = [-(length / 2 - flange_len / 2), length / 2 - flange_len / 2])
                translate([0, 0, z])
                    difference() {
                        cylinder(h = flange_len, d = flange_od, center = true);
                        cylinder(h = flange_len + 1, d = winding_d, center = true);
                    }
        }
        for (sign = [-1, 1]) {
            radial_cut(m4_d, sign * (length / 2 - flange_len / 2));
            radial_cut(lead_d, lead_z(sign));
        }
    }
}

module preview_winding() {
    difference() {
        cylinder(h = winding_len, d = winding_d + 2 * od, center = true);
        cylinder(h = winding_len + 1, d = winding_d, center = true);
    }
}

module preview_shrink() {
    difference() {
        cylinder(h = length, d = flange_od + 2 * shrink_wall, center = true);
        cylinder(h = length + 1, d = flange_od, center = true);
    }
}

module echo_recipe() {
    if (!geometry_ok) {
        echo("ОШИБКА: неверные параметры (стенка, L или провод). Геометрию не строим.");
        echo("inner_d=", inner_d, " N_exact=", N_exact, " winding_len=", winding_len);
    } else {
        echo("Витки N=", N, " (точно ", N_exact, ")");
        echo("Окно намотки мм=", winding_len);
        echo("L факт мкГн=", L_actual);
        echo("Длина каркаса мм=", length);
        echo("Ø буртика мм=", flange_od);
        echo("Ø канала мм=", inner_d);
        echo("Ø отвода мм=", lead_d, " Ø М4 мм=", m4_d);
        echo("Мин. внутр. Ø термоусадки до усадки мм=", flange_od + 2);
        echo("Сборка: лак → отводы на М4 (гайка в канале) → усадка на всю катушку, болты снаружи");
        if (lead_d >= flange_od / 2)
            echo("ПРЕДУПРЕЖДЕНИЕ: отверстие отвода очень большое относительно каркаса");
    }
}

echo_recipe();

if (geometry_ok) {
    former();
    if ($preview && show_winding)
        color("gold", 0.7) preview_winding();
    if ($preview && show_shrink)
        color("silver", 0.35) preview_shrink();
}
