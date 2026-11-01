"""
Feature: visual troubleshooting (photo half).

Customer uploads a photo of their router/ONT/set-top box. We read the
dominant color of the indicator-light region using Pillow's color
quantization, and map it to a diagnosis using the near-universal telecom
hardware convention (green/blue = OK, red = fault, amber/orange = no
upstream signal, mostly dark = powered off).

This is a deliberately lightweight first version -- good enough to demo
end-to-end "upload a photo, get a diagnosis" flow. A stronger version
would train a small CNN classifier on labeled router-light photos (the
function signature below is written so that swap is a drop-in change:
keep returning the same dict shape).
"""
from PIL import Image

# (name, hue-center-degrees, diagnosis)
COLOR_DIAGNOSES = [
    ("red", 0, "The device is signaling a fault. Try power-cycling it: unplug for 30 seconds, then plug back in. If red persists, it's likely a line/hardware fault that needs a technician visit."),
    ("amber", 35, "The light indicates the device is on but not getting an upstream signal -- this usually means an outage on our end or a loose cable. Check the cable connections first."),
    ("green", 120, "This indicates normal operation. If you're still facing issues, the problem is likely with your specific device's Wi-Fi settings rather than the connection itself."),
    ("blue", 220, "This typically indicates the device is online and connected normally."),
]


def _dominant_hue(image: Image.Image):
    small = image.convert("RGB").resize((60, 60))
    colors = small.getcolors(60 * 60)  # [(count, (r,g,b)), ...]
    if not colors:
        return None, 0
    colors.sort(reverse=True, key=lambda c: c[0])

    # skip near-black / near-white / near-gray pixels (background, casing)
    for count, (r, g, b) in colors:
        mx, mn = max(r, g, b), min(r, g, b)
        brightness = (r + g + b) / 3
        saturation = 0 if mx == 0 else (mx - mn) / mx
        if saturation > 0.35 and 20 < brightness < 235:
            hue = _rgb_to_hue(r, g, b)
            return hue, count
    return None, 0


def _rgb_to_hue(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        return 0
    if mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h * 60


def diagnose_image(file_storage) -> dict:
    try:
        image = Image.open(file_storage.stream)
    except Exception:
        return {"success": False, "diagnosis": None, "detected_color": None, "error": "Couldn't read that image -- please upload a JPG or PNG photo."}

    hue, pixel_count = _dominant_hue(image)

    if hue is None:
        return {
            "success": True,
            "detected_color": "unclear",
            "diagnosis": "Couldn't clearly identify an indicator light in this photo. Try taking the photo closer to the light, in a dimmer room, so the LED color stands out.",
        }

    closest = min(COLOR_DIAGNOSES, key=lambda c: min(abs(hue - c[1]), 360 - abs(hue - c[1])))
    name, _, diagnosis = closest

    return {
        "success": True,
        "detected_color": name,
        "diagnosis": diagnosis,
    }
