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


def derived(L_uH, winding_d, wire_cu_d, wire_od, wall, flange_len, flange_over_wire, lead_d=1.5, spare_turns=1):
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
    ok = inner_d > 0 and finite and winding_len > 0 and spare_turns >= 0
    L_actual = wheeler_L(N, r_mm, pitch) if ok else float("nan")
    remaining = winding_len - 2 * lead_d - 2
    use_mid_leads = remaining < lead_d
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
        "L_actual": L_actual,
        "shrink_id_min": flange_od + 2,
        "use_mid_leads": use_mid_leads,
        "ok": ok,
    }
