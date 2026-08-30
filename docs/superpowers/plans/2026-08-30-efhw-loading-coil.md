# План: параметрический каркас катушки EFHW

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Один файл OpenSCAD с Customizer считает однослойную катушку 100 мкГн (ПЭТВ-2 1 мм, Ø намотки 55 мм) и печатает только каркас.

**Architecture:** Эталон формул — Python (`tests/coil_math.py`). OpenSCAD повторяет те же функции и строит трубу + буртики + отверстия; обмотка и термоусадка только в F5.

**Tech Stack:** Python 3 (unittest), OpenSCAD 2021+ (`assert`, `$preview`, Customizer).

**Spec:** `docs/superpowers/specs/2026-08-30-efhw-loading-coil-design.md`

## Global Constraints

- Один модель-файл: `EFHW_Loading_Coil_100_mkgn_1mm.scad`, без `include`
- STL всегда только каркас; превью только при `$preview && show_*`
- Комментарии в `.scad` на русском
- Однослойно, виток к витку, канал сквозной
- Отверстия с одной стороны (−Y), не на весь диаметр
- Если git-репозитория нет — шаги `git commit` пропустить (не делать `git init`, пока пользователь не попросил)

---

### Task 1: Эталон формул Уилера

**Files:**
- Create: `tests/coil_math.py`
- Create: `tests/test_coil_math.py`

**Interfaces:**
- Consumes: spec, раздел «Производная геометрия» и «Уилер 1928»
- Produces: `in_from_mm(mm)`, `petv2_od(cu_d)`, `wire_od_eff(cu_d, od)`, `wheeler_n(L, r_mm, pitch_mm)`, `wheeler_L(N, r_mm, pitch_mm)`, `derived(L_uH, winding_d, wire_cu_d, wire_od, wall, flange_len, flange_over_wire)` → dict

- [ ] **Step 1: Написать падающие тесты**

```python
# tests/test_coil_math.py
import unittest
from coil_math import derived, petv2_od, wire_od_eff


class TestCoilMath(unittest.TestCase):
    def test_petv2_1mm(self):
        self.assertAlmostEqual(petv2_od(1.0), 1.093, places=6)
        self.assertAlmostEqual(wire_od_eff(1.0, 0), 1.093, places=6)
        self.assertAlmostEqual(wire_od_eff(1.0, 1.12), 1.12, places=6)

    def test_defaults_wheeler(self):
        d = derived(100, 55, 1.0, 0, 2, 14.5, 0.5)
        self.assertEqual(d["N"], 51)
        self.assertAlmostEqual(d["N_exact"], 51.21, places=2)
        self.assertAlmostEqual(d["winding_len"], 55.743, places=3)
        self.assertAlmostEqual(d["L_actual"], 99.46, places=2)
        self.assertAlmostEqual(d["flange_od"], 58.186, places=3)
        self.assertAlmostEqual(d["length"], 84.743, places=3)
        self.assertAlmostEqual(d["inner_d"], 51.0, places=3)
        self.assertAlmostEqual(d["lead_d"], 2.186, places=3)
        self.assertAlmostEqual(d["shrink_id_min"], 60.186, places=3)
        self.assertTrue(d["ok"])

    def test_L50_fewer_turns(self):
        d = derived(50, 55, 1.0, 0, 2, 14.5, 0.5)
        self.assertEqual(d["N"], 31)
        self.assertLess(d["length"], 84.743)

    def test_measured_wire_od(self):
        d = derived(100, 55, 1.0, 1.12, 2, 14.5, 0.5)
        self.assertAlmostEqual(d["pitch"], 1.12, places=6)
        self.assertAlmostEqual(d["lead_d"], 2.24, places=6)
        self.assertGreater(d["flange_od"], 58.186)

    def test_bad_wall(self):
        d = derived(100, 55, 1.0, 0, 30, 14.5, 0.5)
        self.assertFalse(d["ok"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Запустить тесты — должны упасть**

Run: `python3 -m unittest tests.test_coil_math -v` из корня репозитория  
(если `ModuleNotFoundError`, запускать `cd tests && python3 -m unittest test_coil_math -v`)

Expected: FAIL (`No module named coil_math` или `cannot import derived`)

- [ ] **Step 3: Минимальная реализация**

```python
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


def derived(L_uH, winding_d, wire_cu_d, wire_od, wall, flange_len, flange_over_wire):
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
    winding_len = N * pitch
    length = winding_len + 2 * flange_len
    flange_od = winding_d + 2 * (od + flange_over_wire)
    lead_d = 2 * od
    ok = inner_d > 0 and finite and winding_len > 0
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
```

- [ ] **Step 4: Тесты должны пройти**

Run: `cd tests && python3 -m unittest test_coil_math -v`

Expected: `OK`, 5 tests.

- [ ] **Step 5: Commit** (пропустить, если нет git)

```bash
git add tests/coil_math.py tests/test_coil_math.py
git commit -m "$(cat <<'EOF'
test: эталон Уилера для каркаса EFHW

EOF
)"
```

---

### Task 2: Параметры Customizer, функции и echo в OpenSCAD

**Files:**
- Modify: `EFHW_Loading_Coil_100_mkgn_1mm.scad` (полная замена содержимого; геометрия пока заглушка)

**Interfaces:**
- Consumes: те же сигнатуры, что в `tests/coil_math.py`
- Produces: функции `in_from_mm`, `petv2_od`, `wire_od_eff`, `wheeler_n`, `wheeler_L`; переменные `od`, `inner_d`, `pitch`, `r_mm`, `N_exact`, `N`, `winding_len`, `length`, `flange_od`, `lead_d`, `L_actual`, `use_mid_leads`, `geometry_ok`

- [ ] **Step 1: Заменить файл каркасом без твёрдого тела** (чтобы сверить echo)

Полностью переписать `EFHW_Loading_Coil_100_mkgn_1mm.scad`:

```openscad
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

// Заглушка Task 2: точка, чтобы файл открывался. Заменить в Task 3.
if (geometry_ok)
    sphere(d = 0.1);
```

- [ ] **Step 2: Сверить echo с Python**

Run:

```bash
cd tests && python3 -c "from coil_math import derived; d=derived(100,55,1.0,0,2,14.5,0.5); print(d['N'], d['L_actual'], d['length'], d['flange_od'])"
```

Expected: `51 99.46... 84.743 58.186`

Открыть `.scad` в OpenSCAD, F5, консоль: `N= 51`, `L факт` ≈ 99.46, длина ≈ 84.743, Ø буртика ≈ 58.186. Расхождение > 1 витка или > 5 мкГн = ошибка порта.

Если есть CLI: `openscad -o /tmp/coil-stub.stl EFHW_Loading_Coil_100_mkgn_1mm.scad` — в stderr те же echo.

- [ ] **Step 3: Commit** (пропустить, если нет git)

```bash
git add EFHW_Loading_Coil_100_mkgn_1mm.scad
git commit -m "$(cat <<'EOF'
feat: параметрический расчёт Уилера в OpenSCAD

EOF
)"
```

---

### Task 3: Твёрдое тело каркаса

**Files:**
- Modify: `EFHW_Loading_Coil_100_mkgn_1mm.scad` (заменить заглушку `sphere` на `former()`)

**Interfaces:**
- Consumes: `length`, `winding_d`, `inner_d`, `flange_len`, `flange_od`, `m4_d`, `lead_d`, `use_mid_leads`, `winding_len`, `geometry_ok`
- Produces: `module former()`, `module radial_cut(d, z)`, `function lead_z(sign)`

- [ ] **Step 1: Добавить геометрию, убрать sphere**

Вставить **перед** `echo_recipe();` и заменить блок `if (geometry_ok) sphere...` на вызов `former()`:

```openscad
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

echo_recipe();

if (geometry_ok)
    former();
```

`rotate([90,0,0])` + `center=false` даёт цилиндр в −Y (как в старом файле).

- [ ] **Step 2: Проверить F5**

С дефолтами:

- одна полая труба, два буртика, канал насквозь
- четыре отверстия с одной стороны (−Y)
- М4 в центре каждого буртика
- отводы сразу за буртиком в окне намотки
- нет обмотки и усадки

Сменить `L_uH` на 50: каркас короче, отверстия всё ещё с одной стороны и в окне.

`wire_od = 1.12`: буртик и отводы толще.

- [ ] **Step 3: Commit** (пропустить, если нет git)

```bash
git add EFHW_Loading_Coil_100_mkgn_1mm.scad
git commit -m "$(cat <<'EOF'
feat: печатный каркас трубы с буртиками и отверстиями

EOF
)"
```

---

### Task 4: Превью обмотки и термоусадки

**Files:**
- Modify: `EFHW_Loading_Coil_100_mkgn_1mm.scad`

**Interfaces:**
- Consumes: `show_winding`, `show_shrink`, `shrink_wall`, `$preview`, размеры из Task 2
- Produces: `module preview_winding()`, `module preview_shrink()`

- [ ] **Step 1: Добавить модули превью и вызовы**

После `module former()`:

```openscad
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
```

Вызов в конце файла:

```openscad
echo_recipe();

if (geometry_ok) {
    former();
    if ($preview && show_winding)
        color("gold", 0.7) preview_winding();
    if ($preview && show_shrink)
        color("silver", 0.35) preview_shrink();
}
```

- [ ] **Step 2: Проверить превью и F6**

- `show_winding=true`, F5: золотая трубка между буртиками, не спираль
- `show_shrink=true`, F5: полупрозрачная оболочка на всю длину, включая буртики
- F6 (Render): превью нет; один manifold-каркас
- CLI при наличии: `openscad -o /tmp/efhw-former.stl EFHW_Loading_Coil_100_mkgn_1mm.scad` — STL создаётся, в логе рецепт сборки

- [ ] **Step 3: Commit** (пропустить, если нет git)

```bash
git add EFHW_Loading_Coil_100_mkgn_1mm.scad
git commit -m "$(cat <<'EOF'
feat: превью обмотки и термоусадки только в F5

EOF
)"
```

---

### Task 5: Ошибка геометрии и финальная сверка

**Files:**
- Modify: `EFHW_Loading_Coil_100_mkgn_1mm.scad` только если guard не срабатывает
- Test: `tests/test_coil_math.py` (уже есть `test_bad_wall`)

**Interfaces:**
- Consumes: `geometry_ok`
- Produces: при `wall = 30` (или `winding_d = 3`) — нет `former()`, только echo ошибки

- [ ] **Step 1: Проверить guard в OpenSCAD**

Customizer: `wall = 30`, F5. Ожидание: пустой вид (нет трубы), консоль `ОШИБКА: неверные параметры`. Вернуть `wall = 2`.

- [ ] **Step 2: Прогнать unittest ещё раз**

Run: `cd tests && python3 -m unittest test_coil_math -v`

Expected: `OK`

- [ ] **Step 3: Чеклист spec**

- [ ] F5 дефолт: труба, два буртика, 4 отверстия, −Y, без превью
- [ ] F5 превью: обмотка в окне, усадка на буртики
- [ ] F6: только каркас
- [ ] echo ≈ N=51, L≈99.46 мкГн, length≈84.7, flange_od≈58.2
- [ ] `L_uH=50` → N=31, короче
- [ ] `wire_od=1.12` → pitch/lead/flange следуют
- [ ] сквозной канал, буртики только снаружи

- [ ] **Step 4: Commit** (пропустить, если нет git)

```bash
git add EFHW_Loading_Coil_100_mkgn_1mm.scad tests
git commit -m "$(cat <<'EOF'
fix: guard невалидной геометрии каркаса EFHW

EOF
)"
```
