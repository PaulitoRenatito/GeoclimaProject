"""Value-to-color scale shared by the bar chart and the map, so both tabs read the same way."""

from matplotlib import colormaps
from matplotlib.colors import Normalize, to_hex

from geoclima.weather.application.analysis import Metric

# Rain and humidity read better on a single-hue scale; temperatures and wind on cold-to-hot.
SEQUENTIAL = {"precipitation", "humidity_avg"}


def value_colors(values: list[float], metric: Metric) -> list[str]:
    if not values:
        return []
    low, high = min(values), max(values)
    norm = Normalize(vmin=low, vmax=high if high > low else low + 1)
    if metric.field in SEQUENTIAL:
        cmap, start = colormaps["Blues"], 0.35  # the palest blues vanish on light and dark backgrounds
    else:
        cmap, start = colormaps["coolwarm"], 0.0
    return [to_hex(cmap(start + (1 - start) * float(norm(value)))) for value in values]
