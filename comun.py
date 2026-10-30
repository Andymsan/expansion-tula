import os, urllib.request
import numpy as np
import ee

CRS = "EPSG:32614"
MUNICIPIO = ("Hidalgo", "Tula De Allende")  # FAO/GAUL/2025/level2 (la versión 2015 da 491 km²)
DW_CLASES = ["agua", "árboles", "pastizal", "vegetación inundable", "cultivos", "matorral", "construido", "suelo desnudo", "nieve"]
NATURAL = [1, 2, 3, 5]
INICIO, FIN = (2016, 2017), (2025, 2026)  # pares de años para comparar en los mapas (Dynamic World)


def municipio():
    return (ee.FeatureCollection("FAO/GAUL/2025/level2")
            .filter(ee.Filter.eq("GAUL1_NAME", MUNICIPIO[0])).filter(ee.Filter.eq("GAUL2_NAME", MUNICIPIO[1])))


def dw(años, geom):
    c = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(geom)
    return c.filterDate(f"{años[0]}-01-01", f"{años[-1] + 1}-01-01").select("label").mode()


def dw_areas(año, geom):
    h = dw((año,), geom).reduceRegion(ee.Reducer.frequencyHistogram(), geom, 10, crs=CRS, maxPixels=1e10).getInfo()["label"]
    return {DW_CLASES[int(k)]: v * 0.01 for k, v in h.items()}  # celdas de 10 m → ha


def descargar(img, region, escala, ruta):
    url = img.getDownloadURL({"region": region, "crs": CRS, "scale": escala, "format": "GEO_TIFF"})
    urllib.request.urlretrieve(url, ruta)


def leer(ruta):
    import rasterio
    with rasterio.open(ruta) as r:
        z, b = r.read(1), r.bounds
    os.remove(ruta)
    return z, [b.left, b.right, b.bottom, b.top]


def base(mun, out, magoni):
    """Relieve, límite, áreas protegidas y Cerro Magoni, en EPSG:32614."""
    import geopandas as gpd
    geom = mun.geometry()
    region = geom.bounds(1).buffer(1500, 10)
    dem = ee.Image("NASA/NASADEM_HGT/001").select("elevation")
    descargar(ee.Terrain.hillshade(dem.multiply(3)).toByte(), region, 30, f"{out}/_relieve.tif")
    relieve = leer(f"{out}/_relieve.tif")
    a2g = lambda fc: gpd.GeoDataFrame.from_features(fc.getInfo()["features"], crs="EPSG:4326").to_crs(CRS)
    anp = a2g(ee.FeatureCollection("WCMC/WDPA/current/polygons").filterBounds(geom).select(["NAME", "DESIG"]))
    anp = anp.clip(a2g(mun)).dissolve("NAME").reset_index()
    return {"relieve": relieve, "municipio": a2g(mun), "anp": anp, "magoni": gpd.read_file(magoni).to_crs(CRS), "region": region}


def dibujar(ax, b, titulo, subtitulo):
    from matplotlib.patches import FancyArrow
    z, ext = b["relieve"]
    ax.imshow(z, cmap="gray", extent=ext, vmin=60, vmax=255, alpha=0.18, zorder=0)
    lim = b["municipio"]
    x0, y0, x1, y1 = lim.total_bounds
    ax.set_xlim(x0 - 600, x1 + 600); ax.set_ylim(y0 - 600, y1 + 600)
    ax.set_axis_off()
    fuera = lim.envelope.buffer(4000).difference(lim.union_all())
    fuera.plot(ax=ax, color="white", alpha=0.6, lw=0, zorder=4)
    lim.boundary.plot(ax=ax, color="#222222", lw=1, zorder=6)
    b["anp"].plot(ax=ax, facecolor="none", edgecolor="#2e7d32", lw=1, hatch="////", zorder=6)
    b["magoni"].plot(ax=ax, facecolor="none", edgecolor="#6a1b9a", lw=1.4, zorder=6)
    for g, txt, c in [(b["magoni"], "Cerro Magoni", "#6a1b9a"),
                      (b["anp"][b["anp"].NAME == "Tula"], "P. N. Tula", "#2e7d32")]:
        if len(g):
            p = g.union_all().representative_point()
            ax.annotate(txt, (p.x, p.y), xytext=(10, 6), textcoords="offset points", fontsize=6.5, color=c,
                        weight="bold", zorder=8, path_effects=_halo())
    ax.add_patch(FancyArrow(x1 - 300, y1 - 2400, 0, 1400, width=60, head_width=500, head_length=600,
                            color="#222222", zorder=8))
    ax.text(x1 - 300, y1 - 2900, "N", ha="center", fontsize=9, weight="bold", zorder=8)
    ax.set_title(titulo, loc="left", fontsize=13, weight="bold", pad=18)
    ax.text(0, 1.01, subtitulo, transform=ax.transAxes, fontsize=9, color="#555555")


def _halo():
    import matplotlib.patheffects as pe
    return [pe.withStroke(linewidth=2.5, foreground="white")]


def leyenda_base():
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    return [Line2D([0], [0], color="#222222", lw=1, label="Límite municipal"),
            Patch(facecolor="none", edgecolor="#2e7d32", hatch="////", label="Áreas protegidas (WDPA)"),
            Patch(facecolor="none", edgecolor="#6a1b9a", lw=1.4, label="Cerro Magoni")]


def guardar(fig, ax, ruta, fuente):
    ax.text(0, -0.01, fuente, transform=ax.transAxes, va="top", fontsize=7, color="#777777")
    fig.savefig(ruta, dpi=160, bbox_inches="tight", facecolor="white")


def pct(a, b):
    return (b / a - 1) * 100 if a else np.nan
