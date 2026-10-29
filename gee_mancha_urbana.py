import sys, os, urllib.request
import ee

AÑOS = [2000, 2005, 2010, 2015, 2020]
UMBRAL = 0.20               # fracción construida de la celda para contar como mancha
SENSIBILIDAD = [0.10, 0.30]
POBLACION = (86840, 115107)  # INEGI 2000, 2020
MUNICIPIO = ("Hidalgo", "Tula De Allende")  # FAO/GAUL/2025/level2 (la versión 2015 da 491 km²)
CRS = "EPSG:32614"


def mancha(a, u):
    b = ee.Image(f"JRC/GHSL/P2023A/GHS_BUILT_S/{a}").select("built_surface")
    return b.gte(b.projection().nominalScale().pow(2).multiply(u))


def main(gpkg, capa, out, proyecto):
    import geopandas as gpd, pandas as pd, rasterio
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D

    os.makedirs(out, exist_ok=True)
    ee.Initialize(project=proyecto)
    mun = (ee.FeatureCollection("FAO/GAUL/2025/level2")
           .filter(ee.Filter.eq("GAUL1_NAME", MUNICIPIO[0])).filter(ee.Filter.eq("GAUL2_NAME", MUNICIPIO[1])))
    geom = mun.geometry()
    proj = ee.Image("JRC/GHSL/P2023A/GHS_BUILT_S/2000").projection()
    km2 = geom.area(1).divide(1e6).getInfo()

    def suma(img):
        return img.multiply(ee.Image.pixelArea()).reduceRegion(ee.Reducer.sum(), geom, crs=proj, maxPixels=1e9)

    filas = []
    for a in AÑOS:
        b = ee.Image(f"JRC/GHSL/P2023A/GHS_BUILT_S/{a}").select("built_surface")
        r = {"año": a,
             "construida_ha": b.reduceRegion(ee.Reducer.sum(), geom, crs=proj, maxPixels=1e9).getNumber("built_surface")}
        for u in [UMBRAL] + SENSIBILIDAD:
            r[f"mancha_{u:.0%}"] = suma(mancha(a, u)).getNumber("built_surface")
        filas.append({k: (v if k == "año" else v.getInfo() / 1e4) for k, v in r.items()})
    t = pd.DataFrame(filas)
    t[["año", "construida_ha", f"mancha_{UMBRAL:.0%}"]].round(1).rename(
        columns={f"mancha_{UMBRAL:.0%}": "mancha_urbana_ha"}).to_csv(f"{out}/mancha_urbana.csv", index=False)

    i, f = t.iloc[0], t.iloc[-1]
    pct = lambda c: (f[c] / i[c] - 1) * 100
    print(f"Municipio: {km2:.1f} km² (INEGI ~305 km²)")
    print(t.round(1).to_string(index=False))
    print(f"\n{AÑOS[0]}–{AÑOS[-1]}")
    print(f"  Población (INEGI)          {(POBLACION[1] / POBLACION[0] - 1) * 100:+.1f}%")
    print(f"  Superficie construida      {pct('construida_ha'):+.1f}%")
    for u in [UMBRAL] + SENSIBILIDAD:
        print(f"  Mancha urbana (>= {u:.0%})    {pct(f'mancha_{u:.0%}'):+.1f}%")

    m0, m1 = mancha(AÑOS[0], UMBRAL), mancha(AÑOS[-1], UMBRAL)
    clase = m0.where(m1.And(m0.Not()), 2).rename("clase").toByte().clip(geom)
    region = geom.bounds(1).buffer(500, 10)
    url = clase.getDownloadURL({"region": region, "crs": CRS, "scale": 100, "format": "GEO_TIFF"})
    tif = f"{out}/mancha_urbana.tif"
    urllib.request.urlretrieve(url, tif)
    with rasterio.open(tif) as r:
        z, b = r.read(1), r.bounds
    os.remove(tif)
    lim = gpd.GeoDataFrame.from_features(mun.getInfo()["features"], crs="EPSG:4326").to_crs(CRS)
    bordos = gpd.read_file(gpkg, layer=capa).to_crs(CRS)

    c0, c1 = "#9a9a9a", "#e0590c"
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.imshow(z, cmap=ListedColormap(["none", c0, c1]), vmin=0, vmax=2, interpolation="nearest",
              extent=[b.left, b.right, b.bottom, b.top])
    lim.boundary.plot(ax=ax, color="k", lw=0.8)
    bordos.plot(ax=ax, color="#1d74c9", lw=2)
    ax.annotate("Tres Culturas", bordos.union_all().centroid.coords[0], xytext=(8, -4),
                textcoords="offset points", fontsize=9, color="#1d74c9")
    ax.legend(handles=[Patch(color=c0, label=f"Mancha urbana {AÑOS[0]}"),
                       Patch(color=c1, label=f"Crecimiento a {AÑOS[-1]}"),
                       Line2D([0], [0], color="k", lw=0.8, label="Límite municipal"),
                       Line2D([0], [0], color="#1d74c9", lw=2, label="Bordos Tres Culturas")],
              loc="lower left", fontsize=9, frameon=False)
    x0, y0, x1, y1 = lim.total_bounds
    ax.set_xlim(x0 - 300, x1 + 300); ax.set_ylim(y0 - 300, y1 + 300)
    ax.set_axis_off()
    ax.set_title(f"Tula de Allende · mancha urbana {AÑOS[0]}–{AÑOS[-1]} "
                 f"({pct(f'mancha_{UMBRAL:.0%}'):+.0f}%)\nGHSL, celdas de 100 m con ≥ {UMBRAL:.0%} construido",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(f"{out}/mancha_urbana_2000_2020.png", dpi=150)


if __name__ == "__main__":
    main(*sys.argv[1:5])
