import sys, os
import ee
from comun import CRS, municipio, dw, dw_areas, base, dibujar, leyenda_base, guardar, descargar, leer, pct, INICIO, FIN, NATURAL

AÑOS = range(2016, 2027)
HANSEN = "UMD/hansen/global_forest_change_2025_v1_13"
CULTIVOS, CONSTRUIDO = 4, 6
CLASES = {1: ("Vegetación natural que se mantiene", "#74a57f"), 2: ("Perdida: ahora cultivo", "#e9c46a"),
          3: ("Perdida: ahora construido", "#c0392b"), 4: ("Perdida: ahora suelo desnudo o agua", "#9e9e9e"),
          5: ("Recuperada (antes cultivo u otro)", "#b7e4c7")}


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
    nat = ["árboles", "pastizal", "vegetación inundable", "matorral"]

    t = pd.DataFrame([{"año": a, **dw_areas(a, geom)} for a in AÑOS]).fillna(0)
    t["natural"] = t[[c for c in nat if c in t]].sum(axis=1)
    t[["año"] + [c for c in nat if c in t] + ["natural"]].round(1).to_csv(f"{out}/vegetacion_natural_dw.csv", index=False)

    perdida = ee.Image(HANSEN).select("lossyear")
    h = perdida.selfMask().reduceRegion(ee.Reducer.frequencyHistogram(), geom, 30, crs=CRS, maxPixels=1e10).getInfo()["lossyear"]
    hs = pd.DataFrame({"año": [2000 + int(k) for k in h], "perdida_arboles_ha": [v * 0.09 for v in h.values()]})
    hs = hs.set_index("año").reindex(range(2001, 2026), fill_value=0).reset_index().round(1)
    hs.to_csv(f"{out}/perdida_arboles_hansen.csv", index=False)

    a, b = dw(INICIO, geom), dw(FIN, geom)
    n0, n1 = a.remap(NATURAL, [1] * len(NATURAL), 0), b.remap(NATURAL, [1] * len(NATURAL), 0)
    cambio = (ee.Image(0).where(n0.And(n1), 1).where(n0.And(b.eq(CULTIVOS)), 2).where(n0.And(b.eq(CONSTRUIDO)), 3)
              .where(n0.And(n1.Not()).And(b.neq(CULTIVOS)).And(b.neq(CONSTRUIDO)), 4).where(n0.Not().And(n1), 5)
              .selfMask().toByte().rename("c").clip(geom))
    h = cambio.reduceRegion(ee.Reducer.frequencyHistogram(), geom, 10, crs=CRS, maxPixels=1e10).getInfo()["c"]
    ha = {CLASES[int(k)][0]: v * 0.01 for k, v in h.items()}
    pd.Series(ha, name="ha").round(1).rename_axis("cambio").to_csv(f"{out}/vegetacion_natural_cambio.csv")

    v = lambda i: ha.get(CLASES[i][0], 0)
    p0, p1 = v(1) + v(2) + v(3) + v(4), v(1) + v(5)
    rango = lambda p: f"{p[0]}-{p[1]}"
    print(t[["año", "natural"]].round(0).to_string(index=False))
    print(f"\nVegetación natural {rango(INICIO)} -> {rango(FIN)}: {p0:,.0f} -> {p1:,.0f} ha ({pct(p0, p1):+.1f}%)")
    for k, x in ha.items():
        print(f"  {k:<38}{x:>8,.0f} ha")
    print(f"Pérdida de árboles 2001-2025 (Hansen): {hs.perdida_arboles_ha.sum():,.0f} ha")

    bm = base(mun, out, magoni)
    descargar(cambio, bm["region"], 20, f"{out}/_natural.tif")
    z, ext = leer(f"{out}/_natural.tif")

    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.45, 1], wspace=0.2, hspace=0.35)
    ax = fig.add_subplot(gs[:, 0])
    perdida_ha = v(2) + v(3) + v(4)
    dibujar(ax, bm, "Tula de Allende: pérdida de vegetación natural",
            f"{rango(INICIO)} → {rango(FIN)}: se perdieron {perdida_ha:,.0f} ha y se recuperaron {v(5):,.0f} ha "
            f"(balance {pct(p0, p1):+.0f}%)")
    ax.imshow(z, cmap=ListedColormap(["none"] + [c for _, c in CLASES.values()]), vmin=0, vmax=5, extent=ext,
              interpolation="nearest", zorder=2)
    ax.legend(handles=[Patch(color=c, label=n) for n, c in CLASES.values()] + leyenda_base(),
              loc="lower left", fontsize=8.5, framealpha=0.95, edgecolor="none")

    g = fig.add_subplot(gs[0, 1])
    g.plot(t.año, t.natural, color="#3a7d44", lw=2, marker="o", ms=4)
    g.set_ylim(0, t.natural.max() * 1.15)
    g.set_xticks(list(AÑOS)[::2])
    g.set_title("Vegetación natural por año (ha)\nmatorral, pastizal y árboles · Dynamic World", loc="left", fontsize=10, weight="bold")
    g2 = fig.add_subplot(gs[1, 1])
    g2.bar(hs.año, hs.perdida_arboles_ha, color="#7f5539", width=0.75)
    g2.set_title(f"Pérdida de cobertura arbórea por año (ha)\n{hs.perdida_arboles_ha.sum():,.0f} ha en 2001–2025 · Hansen",
                 loc="left", fontsize=10, weight="bold")
    g2.set_xticks(range(2001, 2025, 4))
    for x in (g, g2):
        x.spines[["top", "right"]].set_visible(False)
        x.grid(axis="y", alpha=0.3)
        x.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
    g2.text(0, -0.2, "La biodiversidad no se mide por satélite; la pérdida de hábitat natural\n"
                     "(vegetación que pasa a cultivo, zona construida o suelo desnudo) es su indicador más usado.",
            transform=g2.transAxes, fontsize=8, color="#555555", va="top")
    guardar(fig, ax, f"{out}/vegetacion_natural_2016_2026.png",
            f"Cobertura: Dynamic World (Google, Sentinel-2, 10 m), clase más frecuente en {rango(INICIO)} y {rango(FIN)}.\n"
            f"Árboles: Hansen et al., Global Forest Change v1.13. {FIN[1]} hasta octubre.\n"
            f"Límite: FAO GAUL 2025. Áreas protegidas: WDPA. Relieve: NASADEM.")


if __name__ == "__main__":
    main(*sys.argv[1:4])
