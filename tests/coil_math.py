# tests/coil_math.py
"""Эталон формул каркаса EFHW. OpenSCAD должен совпадать с этими числами."""

MM_PER_IN = 25.4


def in_from_mm(mm):
    return mm / MM_PER_IN


def petv2_od(cu_d):
    return cu_d + 0.093


def wire_od_eff(cu_d, od):
    return petv2_od(cu_d) if od <= 0 else od


def wheeler_n(L, r_mm, pitch_mm):
    r = in_from_mm(r_mm)
    p = in_from_mm(pitch_mm)
    disc = (10 * L * p) ** 2 + 36 * L * (r ** 3)
    return (10 * L * p + disc ** 0.5) / (2 * r * r)


def wheeler_L(N, r_mm, pitch_mm):
    r = in_from_mm(r_mm)
    ell = in_from_mm(N * pitch_mm)
    return (r * r * N * N) / (9 * r + 10 * ell)


def rib_chord_w(inner_d, rib_t):
    r = inner_d / 2
    disc = r * r - (r - rib_t) ** 2
    return 2 * disc ** 0.5 if disc > 0 and rib_t > 0 else 0.0


def derived(
    L_uH,
    winding_d,
    wire_cu_d,
    wire_od,
    wall,
    flange_len,
    flange_over_wire,
    lead_d=1.5,
    spare_turns=8,
    m4_d=4.4,
    rib_t=1,
    lead_flange_gap=0.3,
):
    od = wire_od_eff(wire_cu_d, wire_od)
    inner_d = winding_d - 2 * wall
    pitch = od
    r_mm = (winding_d + od) / 2
    try:
        N_exact = wheeler_n(L_uH, r_mm, pitch)
        finite = N_exact == N_exact and N_exact > 0 and N_exact < 1e6
    except (ZeroDivisionError, ValueError, OverflowError):
        N_exact = float("nan")
        finite = False
    N = max(1, round(N_exact)) if finite else 0
    winding_len = (N + spare_turns) * pitch
    length = winding_len + 2 * flange_len
    flange_od = winding_d + 2 * (od + flange_over_wire)
    rib_w = rib_chord_w(inner_d, rib_t)
    channel_after_rib = inner_d - rib_t
    rib_ok = rib_t > 0 and rib_t < inner_d / 2 and rib_w > m4_d
    ok = inner_d > 0 and finite and winding_len > 0 and spare_turns >= 0 and rib_ok
    L_actual = wheeler_L(N, r_mm, pitch) if ok else float("nan")
    remaining = winding_len - 2 * lead_d - 2 * lead_flange_gap
    use_mid_leads = remaining < lead_d
    lead_z = (winding_len / 4) if use_mid_leads else (winding_len / 2 - lead_d / 2 - lead_flange_gap)
    return {
        "od": od,
        "inner_d": inner_d,
        "pitch": pitch,
        "r_mm": r_mm,
        "N_exact": N_exact,
        "N": N,
        "winding_len": winding_len,
        "length": length,
        "flange_od": flange_od,
        "lead_d": lead_d,
        "m4_d": m4_d,
        "rib_w": rib_w,
        "rib_t": rib_t,
        "channel_after_rib": channel_after_rib,
        "L_actual": L_actual,
        "shrink_id_min": flange_od + 2,
        "use_mid_leads": use_mid_leads,
        "lead_flange_gap": lead_flange_gap,
        "lead_z": lead_z,
        "ok": ok,
    }
