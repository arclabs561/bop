#!/usr/bin/env python3
"""Check color contrast ratios for WCAG compliance"""

def contrast_ratio(rgb1, rgb2):
    """Calculate contrast ratio between two RGB colors"""
    def relative_luminance(rgb):
        r, g, b = [c / 255.0 for c in rgb]
        r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.03928 else r / 12.92
        g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.03928 else g / 12.92
        b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.03928 else b / 12.92
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    l1 = relative_luminance(rgb1)
    l2 = relative_luminance(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

# Colors from CSS
colors = {
    'light': {
        'text': (53, 55, 64),      # --text-primary: #353740
        'bg': (255, 255, 255),     # --bg-primary: #ffffff
        'accent': (16, 163, 127),  # --accent: #10a37f
    },
    'dark': {
        'text': (236, 236, 241),   # --text-primary: #ececf1
        'bg': (33, 33, 33),        # --bg-primary: #212121
        'accent': (16, 163, 127),  # --accent: #10a37f
    }
}

print("WCAG Contrast Ratio Check\n")
print("=" * 60)

for mode, cols in colors.items():
    print(f"\n{mode.upper()} MODE:")
    print("-" * 60)
    
    text_bg = contrast_ratio(cols['text'], cols['bg'])
    accent_bg = contrast_ratio(cols['accent'], cols['bg'])
    accent_text = contrast_ratio(cols['accent'], cols['text'])
    
    print(f"Text on Background: {text_bg:.2f}:1")
    print(f"  {'✅' if text_bg >= 4.5 else '❌'} WCAG AA (≥4.5:1)")
    print(f"  {'✅' if text_bg >= 7.0 else '❌'} WCAG AAA (≥7:1)")
    
    print(f"\nAccent on Background: {accent_bg:.2f}:1")
    print(f"  {'✅' if accent_bg >= 3.0 else '❌'} WCAG AA Large Text (≥3:1)")
    print(f"  {'✅' if accent_bg >= 4.5 else '❌'} WCAG AA Normal Text (≥4.5:1)")

