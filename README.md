# Expansión urbana de Tula de Allende 2000–2026

Entre 2000 y 2020, la población del municipio creció 33% (INEGI) y su mancha urbana 32% (GHSL).

## Mancha urbana

![Mancha urbana 2000–2026](resultados/mancha_urbana_degradado.png)

## Crecimiento 2000–2020

| | 2000 | 2020 | Cambio |
|---|---:|---:|---:|
| Población (INEGI) | 86,840 hab | 115,107 hab | +32.6% |
| Superficie construida | 1,014 ha | 1,367 ha | +34.8% |
| Mancha urbana (≥ 20%) | 2,236 ha | 2,951 ha | +32.0% |

## Por año

| Año | Superficie construida (ha) | No residencial (ha) | Mancha urbana (ha) |
|---|---:|---:|---:|
| 2000 | 1,014 | 29 | 2,236 |
| 2005 | 1,057 | 30 | 2,344 |
| 2010 | 1,107 | 31 | 2,462 |
| 2015 | 1,187 | 33 | 2,579 |
| 2020 | 1,367 | 41 | 2,951 |

La superficie construida incluye uso residencial y no residencial. GHSL clasifica como no residencial solo el 3% del total, lo que subestima la refinería Miguel Hidalgo y la termoeléctrica: la mayor parte de la industria queda contada dentro de la mancha sin separarse.

## Sensibilidad al umbral

| Celdas con construido ≥ | Mancha 2000 (ha) | Mancha 2020 (ha) | Cambio |
|---|---:|---:|---:|
| 10% | 3,419 | 4,438 | +29.8% |
| 20% | 2,236 | 2,951 | +32.0% |
| 30% | 1,309 | 1,841 | +40.7% |

## 2020–2026

GHSL llega a 2020. Para los años siguientes se usa Dynamic World (10 m), que mide la clase "construido" de forma distinta, por lo que la cifra es indicativa y no se suma a la serie de GHSL.

| | 2020 | 2026 | Cambio |
|---|---:|---:|---:|
| Construido (Dynamic World) | 5,573 ha | 5,786 ha | +3.8% |

En el mapa, el rojo marca lo que pasó a construido entre 2019–2020 y 2025–2026 fuera de la mancha GHSL 2020.

## Tierra agrícola

![Tierra agrícola 2016–2026](resultados/tierra_agricola_2016_2026.png)

| Cambio 2016–2017 → 2025–2026 | ha |
|---|---:|
| Cultivo que se mantiene | 6,085 |
| Cultivo nuevo | 965 |
| Cultivo perdido: ahora construido | 222 |
| Cultivo perdido: otro uso | 1,072 |
| **Cultivos 2016–2017 → 2025–2026** | **7,379 → 7,050 (−4.5%)** |

| Año | Cultivos (ha) | Construido (ha) |
|---|---:|---:|
| 2016 | 6,446 | 5,391 |
| 2017 | 7,998 | 5,749 |
| 2018 | 9,028 | 5,354 |
| 2019 | 8,723 | 5,589 |
| 2020 | 9,002 | 5,573 |
| 2021 | 9,244 | 5,956 |
| 2022 | 8,886 | 5,907 |
| 2023 | 9,392 | 5,730 |
| 2024 | 9,224 | 5,860 |
| 2025 | 7,171 | 5,853 |
| 2026 | 6,887 | 5,786 |

- La superficie de cultivo sube y baja con la lluvia: en años secos las parcelas de temporal no se siembran y aparecen como pastizal o suelo desnudo.
- Dynamic World subestima la agricultura: INEGI (2010) reporta 52.9% del municipio como agrícola (~17,800 ha). La tendencia es más confiable que el valor absoluto.

## Vegetación natural

![Vegetación natural 2016–2026](resultados/vegetacion_natural_2016_2026.png)

La biodiversidad no se mide directamente por satélite; se usa la pérdida de hábitat natural (matorral, pastizal y árboles) como indicador.

| Cambio 2016–2017 → 2025–2026 | ha |
|---|---:|
| Vegetación natural que se mantiene | 17,843 |
| Perdida: ahora cultivo | 774 |
| Perdida: ahora construido | 337 |
| Perdida: ahora suelo desnudo o agua | 160 |
| Recuperada (antes cultivo u otro) | 1,675 |
| **Vegetación natural 2016–2017 → 2025–2026** | **19,114 → 19,518 (+2.1%)** |

- Se perdieron 1,271 ha de vegetación natural; 337 ha pasaron a zona construida, de forma permanente.
- La "recuperación" es sobre todo parcelas de temporal que no se sembraron, no regeneración de matorral.
- Pérdida de cobertura arbórea (Hansen, 2001–2025): 56 ha en total; el municipio tiene poca cobertura arbórea densa.

## Método

- Superficie construida: GHSL `JRC/GHSL/P2023A/GHS_BUILT_S`, celdas de 100 m, épocas 2000–2020.
- Mancha urbana: área de las celdas con ≥ 20% de superficie construida.
- Cobertura 2016–2026: Dynamic World `GOOGLE/DYNAMICWORLD/V1`, clase más frecuente de cada año (10 m), áreas calculadas en UTM 14N. Los mapas comparan 2016–2017 con 2025–2026 para reducir el efecto de un solo año. 2026 hasta octubre.
- Pérdida arbórea: Hansen `UMD/hansen/global_forest_change_2025_v1_13`, banda `lossyear`.
- Áreas protegidas: WDPA. Cerro Magoni: `datos/magoni.geojson`. Relieve: NASADEM.
- Límite: `FAO/GAUL/2025/level2`, Tula De Allende (337 km²; INEGI reporta ~305 km²). Con GAUL 2015 (491 km²) el crecimiento de la mancha es +31.7%.

## Tablas

- [Mancha urbana](resultados/mancha_urbana.csv)
- [Cobertura Dynamic World por año](resultados/cobertura_dynamic_world.csv)
- [Cambio en tierra agrícola](resultados/tierra_agricola_cambio.csv)
- [Vegetación natural por año](resultados/vegetacion_natural_dw.csv)
- [Cambio en vegetación natural](resultados/vegetacion_natural_cambio.csv)
- [Pérdida arbórea por año](resultados/perdida_arboles_hansen.csv)

## Archivos

| Archivo | Contenido |
|---|---|
| `comun.py` | Límite municipal, Dynamic World y mapa base compartido |
| `gee_mancha_urbana.py` | Superficie construida, mancha urbana 2000–2020 y construido 2020–2026 |
| `gee_tierra_agricola.py` | Tendencia y cambio de la tierra agrícola 2016–2026 |
| `gee_vegetacion_natural.py` | Tendencia y pérdida de vegetación natural 2016–2026 |
| `datos/magoni.geojson` | Polígono del Cerro Magoni |

## Uso

```
pip install -r requirements.txt
python gee_mancha_urbana.py datos/magoni.geojson resultados <proyecto_gee>
python gee_tierra_agricola.py datos/magoni.geojson resultados <proyecto_gee>
python gee_vegetacion_natural.py datos/magoni.geojson resultados <proyecto_gee>
```
