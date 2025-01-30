# ![image](https://github.com/krbg-TeleDeLuxe/TeleProp/blob/main/TeleDeLuxe.png) TeleProp

## What is this?
This is a QGIS plugin for radio propagation to compute field strength prediction of transmitter.
## Prediction models
- Freespace
- Empirical Two Ray
- Hata
- COST Hata
- Extended Hata
- ITU 1546
- Longley-Rice (ITM)
- ITU 1812

These models are used for broadcasting transmitters, point-multipoint systems, point-point radiolinks.
## Prediction modes
### Point mode
Individual test ponts given by WGS Lat-Lon coords: paste from Excel table, create points from GPS coords or pick from map.
### Limit line mode
Create field strength limits. Where the field strength exceeds the limits every 10° nearest from transmitter, points draw a polygon. Fast method for large areas, mainly used for broadcasting.
### Area mode
Create a rectangular area around transmitter or draw area on map and calculate field strength with wanted resolution for every piece of area. The pieces will be colored by value of field strength for heatmap.
## Necessary external databases
- Digital Elevation Map (DEM) data for example Copernicus Open DEM Europe.
- Optionally Land Cover (clutter) data for example Copernicus Urban Atlas Land Cover Land Use or Corinne Land Cover.
- Transmitter database: optionally you can get data from national authority or create from design data
- Base map layer for example OpenStreetMap, Google Maps tiles.
- Transmitter antenna radiation pattern
## Designed for what use?
Easy to use tool for:
- to predict transmitter coverage area
- to compare with standing state measured data
- to compare with route registration measured data
- to know effect of changing antenna and transmitter parameters

> [!IMPORTANT]
> Works with all meter based project CRS: **'UTM'**,  **'Pseudo Mercator'** or in Hungary **`EPSG:23700`** (HD72 / EOV)

[Install](https://github.com/krbg-TeleDeLuxe/TeleProp/wiki/Installation)

Created by: Lakatos Tamás e-mail: krbg.index@gmail.com
