# TeleProp
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="TeleDeLuxe.png">
  <source media="(prefers-color-scheme: light)" srcset="TeleDeLuxe.png">
  <img alt="TeleDeLuxe logo image" src="TeleDeLuxe.png">
</picture>

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

These models are using for broadcasting transmitters, point-multipoint systems, point-point radiolinks.
## Prediction modes
### Point mode
Individual test ponts given by WGS Lat-Lon coords: paste from Excel table, create points from GPS coords or pick from map.
### Limit line mode
Create fieldstrength limits. Where the fieldstrength exceeds these limits every 10° nearest from transmitter, points draws a polygon. Fast method for large areas, mainly used for broadcasting.
### Area mode

