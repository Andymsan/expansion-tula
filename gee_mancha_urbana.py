import sys, os
import ee
from comun import municipio, dw, dw_areas, base, dibujar, leyenda_base, guardar, descargar, leer, pct

AÑOS = [2000, 2005, 2010, 2015, 2020]
UMBRAL = 0.20               # fracción construida de la celda para contar como mancha
SENSIBILIDAD = [0.10, 0.30]
POBLACION = (86840, 115107)  # INEGI 2000, 2020
DW_RECIENTE = (2020, 2026)   # Dynamic World: construido nuevo después del último año GHSL


def mancha(a, u):
    b = ee.Image(f"JRC/GHSL/P2023A/GHS_BUILT_S/{a}").select("built_surface")
    return b.gte(b.projection().nominalScale().pow(2).multiply(u))


def main(magoni, out, proyecto):
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    os.makedirs(out, exist_ok=True)
    ee.Initialize(project=proyecto)
    mun = municipio()
    geom = mun.geometry()
    proj = ee.Image("JRC/GHSL/P2023A/GHS_BUILT_S/2000").projection()
    km2 = geom.area(1).divide(1e6).getInfo()

    def suma(img, banda="built_surface"):
        return img.multiply(ee.Image.pixelArea()).reduceRegion(ee.Reducer.sum(), geom, crs=proj, maxPixels=1e9).getNumber(banda)

    filas = []
    for a in AÑOS:
        b = ee.Image(f"JRC/GHSL/P2023A/GHS_BUILT_S/{a}")
        s = b.reduceRegion(ee.Reducer.sum(), geom, crs=proj, maxPixels=1e9)
        r = {"año": a, "construida_ha": s.getNumber("built_surface"), "no_residencial_ha": s.getNumber("built_surface_nres")}
        for u in [UMBRAL] + SENSIBILIDAD:
            r[f"mancha_{u:.0%}"] = suma(mancha(a, u))
        filas.append({k: (v if k == "año" else v.getInfo() / 1e4) for k, v in r.items()})
    t = pd.DataFrame(filas)
    t[["año", "construida_ha", "no_residencial_ha", f"mancha_{UMBRAL:.0%}"]].round(1).rename(
        columns={f"mancha_{UMBRAL:.0%}": "mancha_urbana_ha"}).to_csv(f"{out}/mancha_urbana.csv", index=False)

    c0, c1 = (dw_areas(a, geom).get("construido", 0) for a in DW_RECIENTE)
    i, f = t.iloc[0], t.iloc[-1]
    cambio = lambda c: pct(i[c], f[c])
    print(f"Municipio: {km2:.1f} km² (INEGI: 1.62% de Hidalgo ≈ 338 km²)".encode("ascii", "replace").decode())
    print(t.round(1).to_string(index=False))
    print(f"\n{AÑOS[0]}-{AÑOS[-1]}")
    print(f"  Población (INEGI)          {pct(*POBLACION):+.1f}%")
    print(f"  Superficie construida      {cambio('construida_ha'):+.1f}%")
    print(f"  No residencial (GHSL)      {f.no_residencial_ha / f.construida_ha:.0%} del total en {AÑOS[-1]}")
    for u in [UMBRAL] + SENSIBILIDAD:
        print(f"  Mancha urbana (>= {u:.0%})    {cambio(f'mancha_{u:.0%}'):+.1f}%")
    print(f"\n{DW_RECIENTE[0]}-{DW_RECIENTE[1]} (Dynamic World, indicativo)")
    print(f"  Construido                 {c0:,.0f} -> {c1:,.0f} ha ({pct(c0, c1):+.1f}%)")

    b = base(mun, out, magoni)
    m0, m1 = mancha(AÑOS[0], UMBRAL), mancha(AÑOS[-1], UMBRAL)
    clase = m0.where(m1.And(m0.Not()), 2).selfMask().rename("clase").toByte().clip(geom)
    descargar(clase, b["region"], 100, f"{out}/_ghsl.tif")
    nuevo = (dw((DW_RECIENTE[1] - 1, DW_RECIENTE[1]), geom).eq(6)
             .And(dw((DW_RECIENTE[0] - 1, DW_RECIENTE[0]), geom).neq(6))
             .And(m1.reproject(proj).Not()).selfMask().toByte().clip(geom))
    descargar(nuevo, b["region"], 20, f"{out}/_dw.tif")
    (zg, eg), (zd, ed) = leer(f"{out}/_ghsl.tif"), leer(f"{out}/_dw.tif")

    col = {"2000": "#4a4a4a", "2020": "#f28e2b", "2026": "#c0392b"}
    fig, ax = plt.subplots(figsize=(9, 10.5))
    dibujar(ax, b, "Tula de Allende: crecimiento de la mancha urbana",
            f"Mancha {AÑOS[0]}–{AÑOS[-1]}: {cambio(f'mancha_{UMBRAL:.0%}'):+.0f}% (GHSL) · población {pct(*POBLACION):+.0f}% (INEGI)")
    ax.imshow(zg, cmap=ListedColormap(["none", col["2000"], col["2020"]]), vmin=0, vmax=2, extent=eg,
              interpolation="nearest", zorder=2)
    ax.imshow(zd, cmap=ListedColormap(["none", col["2026"]]), vmin=0, vmax=1, extent=ed, interpolation="nearest", zorder=3)
    ax.legend(handles=[Patch(color=col["2000"], label=f"Mancha urbana {AÑOS[0]}"),
                       Patch(color=col["2020"], label=f"Crecimiento {AÑOS[0]}–{AÑOS[-1]}"),
                       Patch(color=col["2026"], label=f"Construido nuevo {DW_RECIENTE[0]}–{DW_RECIENTE[1]}*")] + leyenda_base(),
              loc="lower left", fontsize=8.5, frameon=True, framealpha=0.95, edgecolor="none")
    guardar(fig, ax, f"{out}/mancha_urbana_2000_2026.png",
            f"Mancha urbana: GHSL (JRC), celdas de 100 m con ≥ {UMBRAL:.0%} construido. "
            f"*{DW_RECIENTE[0]}–{DW_RECIENTE[1]}: Dynamic World (10 m), indicativo.\n"
            "Límite: FAO GAUL 2025. Áreas protegidas: WDPA. Relieve: NASADEM.")


if __name__ == "__main__":
    main(*sys.argv[1:4])
