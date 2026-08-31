"""Broadcast-ephemeris propagation and signal-in-space error, for the EphemErr A2 screen.

The label factory: propagate each broadcast navigation record forward exactly as a receiver would,
difference the result against the precise post-processed orbit and clock at the same epochs, and
the residual IS the label - how wrong that broadcast message turned out to be.

The asymmetry this rests on: the precise product is reconstructed days later from a global tracking
network of roughly 500 stations. The broadcast message is the ground segment's forward PREDICTION,
uploaded hours earlier. The manufacturer literally observes the future the student must predict.

Algorithm is the standard GPS user algorithm from IS-GPS-200. GPS only; other constellations use
the same shape with different constants and are out of scope here.
"""
from __future__ import annotations

import gzip
import math
import re

MU = 3.986005e14              # WGS-84 gravitational constant, m^3/s^2
OMEGA_E = 7.2921151467e-5     # WGS-84 earth rotation rate, rad/s
F_REL = -4.442807633e-10      # relativistic correction constant, s/sqrt(m)
C = 299792458.0


def _f(s: str) -> float:
    s = s.strip().replace("D", "E").replace("d", "e")
    return float(s) if s else 0.0


def parse_nav(path: str, sys_char: str = "G") -> list[dict]:
    """RINEX 3 navigation records for one constellation."""
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", errors="ignore") as fh:
        lines = fh.readlines()
    start = next((i for i, l in enumerate(lines) if "END OF HEADER" in l), 0) + 1
    recs, i = [], start
    hdr = re.compile(rf"^{sys_char}(\d\d) (\d{{4}}) (\d\d) (\d\d) (\d\d) (\d\d) (\d\d)")
    while i < len(lines):
        m = hdr.match(lines[i])
        if not m or i + 7 >= len(lines):
            i += 1
            continue
        prn = int(m.group(1))
        y, mo, d, h, mi, s = (int(m.group(k)) for k in range(2, 8))
        blk = lines[i]
        vals = [_f(blk[23:42]), _f(blk[42:61]), _f(blk[61:80])]
        for j in range(1, 8):
            L = lines[i + j].rstrip("\n").ljust(80)
            vals += [_f(L[4:23]), _f(L[23:42]), _f(L[42:61]), _f(L[61:80])]
        if len(vals) < 31:
            i += 8
            continue
        af0, af1, af2 = vals[0], vals[1], vals[2]
        r = {"prn": prn, "toc": (y, mo, d, h, mi, s),
             "af0": af0, "af1": af1, "af2": af2,
             "iode": vals[3], "crs": vals[4], "delta_n": vals[5], "m0": vals[6],
             "cuc": vals[7], "e": vals[8], "cus": vals[9], "sqrt_a": vals[10],
             "toe": vals[11], "cic": vals[12], "omega0": vals[13], "cis": vals[14],
             "i0": vals[15], "crc": vals[16], "omega": vals[17], "omega_dot": vals[18],
             "idot": vals[19], "l2codes": vals[20], "week": vals[21], "l2p": vals[22],
             "ura": vals[23], "health": vals[24], "tgd": vals[25], "iodc": vals[26],
             "ttm": vals[27], "fit": vals[28] if len(vals) > 28 else 0.0}
        recs.append(r)
        i += 8
    return recs


def gps_sow(y, mo, d, h, mi, s) -> tuple[int, float]:
    """(GPS week, seconds of week) for a UTC-ish calendar date, ignoring leap seconds."""
    a = (14 - mo) // 12
    yy = y + 4800 - a
    mm = mo + 12 * a - 3
    jdn = d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045
    days = jdn - 2444245            # JDN of 1980-01-06, the GPS epoch (a Sunday)
    week = days // 7
    sow = (days % 7) * 86400 + h * 3600 + mi * 60 + s
    return week, float(sow)


def propagate(r: dict, t_sow: float):
    """Broadcast record -> (ECEF x, y, z in metres, satellite clock offset in seconds)."""
    a = r["sqrt_a"] ** 2
    if a <= 0:
        return None
    tk = t_sow - r["toe"]
    if tk > 302400:
        tk -= 604800
    elif tk < -302400:
        tk += 604800
    n = math.sqrt(MU / a ** 3) + r["delta_n"]
    mk = r["m0"] + n * tk
    ek = mk
    for _ in range(12):                       # Kepler, Newton-Raphson
        de = (ek - r["e"] * math.sin(ek) - mk) / (1 - r["e"] * math.cos(ek))
        ek -= de
        if abs(de) < 1e-13:
            break
    se, ce = math.sin(ek), math.cos(ek)
    vk = math.atan2(math.sqrt(1 - r["e"] ** 2) * se, ce - r["e"])
    phik = vk + r["omega"]
    s2, c2 = math.sin(2 * phik), math.cos(2 * phik)
    uk = phik + r["cus"] * s2 + r["cuc"] * c2
    rk = a * (1 - r["e"] * ce) + r["crs"] * s2 + r["crc"] * c2
    ik = r["i0"] + r["idot"] * tk + r["cis"] * s2 + r["cic"] * c2
    xp, yp = rk * math.cos(uk), rk * math.sin(uk)
    omk = r["omega0"] + (r["omega_dot"] - OMEGA_E) * tk - OMEGA_E * r["toe"]
    so, co = math.sin(omk), math.cos(omk)
    ci, si = math.cos(ik), math.sin(ik)
    x = xp * co - yp * ci * so
    y = xp * so + yp * ci * co
    z = yp * si

    wk, toc_sow = gps_sow(*r["toc"])
    dt = t_sow - toc_sow
    if dt > 302400:
        dt -= 604800
    elif dt < -302400:
        dt += 604800
    dtsv = (r["af0"] + r["af1"] * dt + r["af2"] * dt * dt
            + F_REL * r["e"] * r["sqrt_a"] * se - r["tgd"])
    return x, y, z, dtsv


def parse_sp3(path: str, sys_char: str = "G") -> dict:
    """{(prn, sow): (x_m, y_m, z_m, clk_s)} from an SP3 file. 999999.999999 means unavailable."""
    op = gzip.open if path.endswith(".gz") else open
    out, sow = {}, None
    with op(path, "rt", errors="ignore") as fh:
        for line in fh:
            if line.startswith("*"):
                p = line[1:].split()
                if len(p) >= 6:
                    _, sow = gps_sow(int(p[0]), int(p[1]), int(p[2]),
                                     int(p[3]), int(p[4]), int(float(p[5])))
            elif line.startswith("P" + sys_char) and sow is not None:
                try:
                    prn = int(line[2:4])
                    x, y, z = float(line[4:18]), float(line[18:32]), float(line[32:46])
                    clk = float(line[46:60])
                except ValueError:
                    continue
                if abs(clk) > 999999.0:
                    continue
                out[(prn, sow)] = (x * 1000.0, y * 1000.0, z * 1000.0, clk * 1e-6)
    return out


def parse_clk(path: str, sys_char: str = "G") -> dict:
    """{(prn, sow): clock_bias_seconds} from a RINEX clock (.CLK) file.

    An orbit-only SP3 carries a coarse clock column; the precise clocks are a separate product and
    are what the label needs. Using the SP3 column instead inflates the apparent clock error by
    roughly a factor of five, which was measured before this parser existed.
    """
    op = gzip.open if path.endswith(".gz") else open
    out = {}
    with op(path, "rt", errors="ignore") as fh:
        for line in fh:
            if not line.startswith("AS " + sys_char):
                continue
            p = line.split()
            if len(p) < 10:
                continue
            try:
                prn = int(p[1][1:])
                _, sow = gps_sow(int(p[2]), int(p[3]), int(p[4]), int(p[5]), int(p[6]),
                                 int(float(p[7])))
                out[(prn, sow)] = float(p[9])
            except (ValueError, IndexError):
                continue
    return out


def rac_error(bx, by, bz, px, py, pz, vel=None):
    """Broadcast-minus-precise, projected onto radial / along-track / cross-track.

    The along-track direction comes from the satellite velocity when one is supplied (obtained by
    propagating one second apart), which is the correct definition. Without it, a geometric
    stand-in orthogonal to radial is used; that mislabels along and cross but leaves SISRE
    unchanged, because the formula weights the two identically.
    """
    rn = math.sqrt(px * px + py * py + pz * pz)
    if rn == 0:
        return None
    ur = (px / rn, py / rn, pz / rn)
    if vel is not None:
        vx, vy, vz = vel
        cx = ur[1] * vz - ur[2] * vy
        cy = ur[2] * vx - ur[0] * vz
        cz = ur[0] * vy - ur[1] * vx
        cn = math.sqrt(cx * cx + cy * cy + cz * cz)
        if cn == 0:
            return None
        uc = (cx / cn, cy / cn, cz / cn)
        ua = (uc[1] * ur[2] - uc[2] * ur[1], uc[2] * ur[0] - uc[0] * ur[2],
              uc[0] * ur[1] - uc[1] * ur[0])
    else:
        hx, hy, hz = (-py, px, 0.0)
        hn = math.sqrt(hx * hx + hy * hy + hz * hz)
        if hn == 0:
            return None
        ua = (hx / hn, hy / hn, hz / hn)
        uc = (ur[1] * ua[2] - ur[2] * ua[1], ur[2] * ua[0] - ur[0] * ua[2],
              ur[0] * ua[1] - ur[1] * ua[0])
    d = (bx - px, by - py, bz - pz)
    return (sum(d[i] * ur[i] for i in range(3)),
            sum(d[i] * ua[i] for i in range(3)),
            sum(d[i] * uc[i] for i in range(3)))


def sisre(dr: float, da: float, dc: float, dclk_m: float) -> float:
    """GPS signal-in-space ranging error with the standard global-average weights."""
    return math.sqrt((0.98 * dr - dclk_m) ** 2 + (da * da + dc * dc) / 49.0)
