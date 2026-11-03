"""Value-to-color scale shared by the bar chart and the map, so both read the same way."""

from geoclima.weather.application.analysis import Metric

RGB = tuple[int, int, int]

# Anchor colors of matplotlib's "coolwarm" (cold to hot) and "Blues" scales, interpolated linearly.
COOLWARM: list[RGB] = [(59, 76, 192), (124, 159, 249), (192, 212, 245), (242, 203, 183), (238, 133, 105), (180, 4, 38)]
BLUES: list[RGB] = [(198, 219, 239), (158, 202, 225), (107, 174, 214), (66, 146, 198), (33, 113, 181), (8, 48, 107)]

# Rain and humidity read better on a single-hue scale; temperatures and wind on cold-to-hot.
SEQUENTIAL = {"precipitation", "humidity_avg"}


def interpolate(anchors: list[RGB], fraction: float) -> str:
    fraction = min(max(fraction, 0.0), 1.0) * (len(anchors) - 1)
    index = min(int(fraction), len(anchors) - 2)
    local = fraction - index
    low, high = anchors[index], anchors[index + 1]
    r, g, b = (round(a + (b - a) * local) for a, b in zip(low, high, strict=True))
    return f"#{r:02x}{g:02x}{b:02x}"


def value_colors(values: list[float], metric: Metric) -> list[str]:
    if not values:
        return []
    low, high = min(values), max(values)
    span = high - low or 1.0
    anchors = BLUES if metric.field in SEQUENTIAL else COOLWARM
    return [interpolate(anchors, (value - low) / span) for value in values]
