import sys, os
import ee
from comun import CRS, municipio, dw, dw_areas, base, dibujar, leyenda_base, guardar, descargar, leer, pct, INICIO, FIN

AÑOS = range(2016, 2027)
CULTIVOS, CONSTRUIDO = 4, 6
CLASES = {1: ("Cultivo que se mantiene", "#e9c46a"), 2: ("Cultivo nuevo", "#8a6d00"),
          3: ("Cultivo perdido: ahora construido", "#c0392b"), 4: ("Cultivo perdido: otro uso", "#9fb7c9")}


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

    t = pd.DataFrame([{"año": a, **dw_areas(a, geom)} for a in AÑOS]).fillna(0).round(1)
    t.to_csv(f"{out}/cobertura_dynamic_world.csv", index=False)

    a, b = dw(INICIO, geom), dw(FIN, geom)
    c0, c1 = a.eq(CULTIVOS), b.eq(CULTIVOS)
    cambio = (ee.Image(0).where(c0.And(c1), 1).where(c0.Not().And(c1), 2)
              .where(c0.And(b.eq(CONSTRUIDO)), 3).where(c0.And(c1.Not()).And(b.neq(CONSTRUIDO)), 4)
              .selfMask().toByte().rename("c").clip(geom))
    h = cambio.reduceRegion(ee.Reducer.frequencyHistogram(), geom, 10, crs=CRS, maxPixels=1e10).getInfo()["c"]
    ha = {CLASES[int(k)][0]: v * 0.01 for k, v in h.items()}
    pd.Series(ha, name="ha").round(1).rename_axis("cambio").to_csv(f"{out}/tierra_agricola_cambio.csv")

    p0 = ha.get(CLASES[1][0], 0) + ha.get(CLASES[3][0], 0) + ha.get(CLASES[4][0], 0)
    p1 = ha.get(CLASES[1][0], 0) + ha.get(CLASES[2][0], 0)
    rango = lambda p: f"{p[0]}-{p[1]}"
    print(t[["año", "cultivos", "construido"]].to_string(index=False))
    print(f"\nCultivos {rango(INICIO)} -> {rango(FIN)}: {p0:,.0f} -> {p1:,.0f} ha ({pct(p0, p1):+.1f}%)")
    for k, v in ha.items():
        print(f"  {k:<36}{v:>8,.0f} ha")

    bm = base(mun, out, magoni)
    descargar(cambio, bm["region"], 20, f"{out}/_agricola.tif")
    z, ext = leer(f"{out}/_agricola.tif")

    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.45, 1], height_ratios=[1, 1], wspace=0.2, hspace=0.35)
    ax = fig.add_subplot(gs[:, 0])
    dibujar(ax, bm, "Tula de Allende: tierra agrícola",
            f"Cultivos {rango(INICIO)} → {rango(FIN)}: {pct(p0, p1):+.0f}% · "
            f"{ha.get(CLASES[3][0], 0):,.0f} ha de cultivo pasaron a zona construida")
    ax.imshow(z, cmap=ListedColormap(["none"] + [c for _, c in CLASES.values()]), vmin=0, vmax=4, extent=ext,
              interpolation="nearest", zorder=2)
    ax.legend(handles=[Patch(color=c, label=n) for n, c in CLASES.values()] + leyenda_base(),
              loc="lower left", fontsize=8.5, framealpha=0.95, edgecolor="none")

    g = fig.add_subplot(gs[0, 1])
    g.plot(t.año, t.cultivos, color="#b08900", lw=2, marker="o", ms=4)
    g.set_title("Cultivos por año (ha)", loc="left", fontsize=10, weight="bold")
    g2 = fig.add_subplot(gs[1, 1])
    g2.plot(t.año, t.construido, color="#c0392b", lw=2, marker="o", ms=4)
    g2.set_title("Zona construida por año (ha)", loc="left", fontsize=10, weight="bold")
    for x in (g, g2):
        x.spines[["top", "right"]].set_visible(False)
        x.grid(axis="y", alpha=0.3)
        x.set_xticks(list(AÑOS)[::2])
        x.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
    g.set_ylim(0, t.cultivos.max() * 1.15); g2.set_ylim(0, t.construido.max() * 1.15)
    g2.text(0, -0.2, "La superficie de cultivo varía con la lluvia: en años secos las parcelas\n"
                     "de temporal no se siembran y aparecen como pastizal o suelo desnudo.",
            transform=g2.transAxes, fontsize=8, color="#555555", va="top")
    guardar(fig, ax, f"{out}/tierra_agricola_2016_2026.png",
            f"Cobertura: Dynamic World (Google, Sentinel-2, 10 m), clase más frecuente en {rango(INICIO)} y {rango(FIN)}.\n"
            f"{FIN[1]} hasta octubre. Límite: FAO GAUL 2025. Áreas protegidas: WDPA. Relieve: NASADEM.")


if __name__ == "__main__":
    main(*sys.argv[1:4])
