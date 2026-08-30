# План: шайба клеммы полотна

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Переписать `EFHW_terminal_saddle_M4.scad` в грибок с седлом под термоусадку и щелью 3 мм под одну жилу П-274М.

**Architecture:** Один файл Customizer. Седло = цилиндр Ø `flange_od + 2*shrink_wall`. Шляпка на `z = gap`. Без `include` каркаса.

**Tech Stack:** OpenSCAD 2021+; CLI `/Applications/OpenSCAD-2021.01.app/Contents/MacOS/OpenSCAD`

**Spec:** `docs/superpowers/specs/2026-08-30-shayba-malaya-design.md`

## Global Constraints

- Один файл `EFHW_terminal_saddle_M4.scad`, без `include`
- STL — одна шайба; на катушку 2 штуки
- Седло по `saddle_od`, не по голому буртику
- Комментарии на русском
- Git нет — шаги commit пропустить

---

### Task 1: Переписать `EFHW_terminal_saddle_M4.scad`

**Files:**
- Modify: `EFHW_terminal_saddle_M4.scad` (полная замена)

**Interfaces:**
- Produces: `saddle_od`, `R`, `geometry_ok`, `module shayba()`, `echo_recipe()`

- [ ] **Step 1: Заменить файл**

```openscad
$fn = $preview ? 64 : 160;

/* [Shayba] */
m4_d = 4.5;
flange_od = 58.186; // голый буртик, echo каркаса
shrink_wall = 0.6;
gap = 3.0; // над усадкой, жила П-274М ≤ 2.3 мм
hat_d = 14;
hat_h = 2.0;
stem_od = 7.6;

saddle_od = flange_od + 2 * shrink_wall;
R = saddle_od / 2;

geometry_ok =
    gap >= 2.3
    && m4_d < stem_od
    && stem_od < hat_d
    && flange_od > 0
    && hat_h > 0
    && shrink_wall >= 0;

module echo_recipe() {
    if (!geometry_ok) {
        echo("ОШИБКА: неверные параметры шайбы. Геометрию не строим.");
        echo("gap=", gap, " m4_d=", m4_d, " stem_od=", stem_od, " hat_d=", hat_d);
    } else {
        echo("Ø М4 мм=", m4_d);
        echo("Ø голого буртика мм=", flange_od);
        echo("Стенка усадки мм=", shrink_wall);
        echo("Ø седла (усадка) мм=", saddle_od);
        echo("Зазор под жилу мм=", gap);
        echo("Ø шляпки мм=", hat_d, " Ø ножки мм=", stem_od);
        echo("Седло под усадку, не под голый пластик. На катушку 2 детали. Жила П-274М ≤ 2.3 мм.");
        echo("Если flange_od/shrink_wall каркаса другие — подставь их сюда.");
    }
}

module shayba() {
    difference() {
        union() {
            translate([0, 0, -2])
                cylinder(h = gap + 2, d = stem_od);
            translate([0, 0, gap])
                cylinder(h = hat_h, d = hat_d);
        }
        translate([0, 0, -3])
            cylinder(h = gap + hat_h + 4, d = m4_d);
        translate([0, 0, -R])
            rotate([90, 0, 0])
                cylinder(h = hat_d + 4, d = saddle_od, center = true);
    }
}

echo_recipe();

if (geometry_ok)
    shayba();
```

- [ ] **Step 2: CLI дефолт**

Run: `/Applications/OpenSCAD-2021.01.app/Contents/MacOS/OpenSCAD -o /tmp/shayba.stl EFHW_terminal_saddle_M4.scad`

Expected: echo `saddle_od` ≈ 59.386, `gap` = 3; STL создан, не пустой.

- [ ] **Step 3: CLI guard**

Run: тот же бинарник `-D gap=2 -o /tmp/shayba-bad.stl EFHW_terminal_saddle_M4.scad`

Expected: echo `ОШИБКА`; top level empty / нет STL.

- [ ] **Step 4: Commit** — пропустить (нет git)
