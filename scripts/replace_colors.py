#!/usr/bin/env python3
"""
Script to replace old color classes with Apple design system colors
"""

import re

# Define file paths
files_to_update = [
    r"E:\google photos\personality2\persona-evolution-simulator-complete\persona-evolution-simulator\frontend\app\persona\[id]\page.tsx",
    r"E:\google photos\personality2\persona-evolution-simulator-complete\persona-evolution-simulator\frontend\app\persona\[id]\ChatBox.tsx",
    r"E:\google photos\personality2\persona-evolution-simulator-complete\persona-evolution-simulator\frontend\components\FeedbackModal.tsx",
    r"E:\google photos\personality2\persona-evolution-simulator-complete\persona-evolution-simulator\frontend\components\PersonaNarrative.tsx",
    r"E:\google photos\personality2\persona-evolution-simulator-complete\persona-evolution-simulator\frontend\components\templates\TemplateDetailsModal.tsx",
    r"E:\google photos\personality2\persona-evolution-simulator-complete\persona-evolution-simulator\frontend\components\templates\SnapshotComparison.tsx",
    r"E:\google photos\personality2\persona-evolution-simulator-complete\persona-evolution-simulator\frontend\components\templates\TemplateBrowser.tsx",
]

# Define replacement patterns (order matters - specific before general)
replacements = [
    # Special opacity variants first
    ('bg-cream/80', 'bg-white/80'),
    ('bg-cream/70', 'bg-white/70'),
    ('bg-clay/20', 'bg-apple-bg-tertiary/20'),
    ('border-charcoal/10', 'border-apple-border-light'),
    ('border-charcoal/20', 'border-apple-border'),
    ('border-moss/30', 'border-apple-blue-200'),
    ('hover:border-moss/30', 'hover:border-apple-blue-200'),

    # Background colors
    ('bg-cream', 'bg-white'),
    ('bg-clay', 'bg-apple-bg-tertiary'),
    ('bg-moss', 'bg-apple-blue-600'),
    ('bg-sage', 'bg-apple-blue-100'),
    ('bg-charcoal', 'bg-apple-bg-primary'),
    ('bg-terracotta', 'bg-red-500'),
    ('bg-grain', 'bg-apple-bg-tertiary gradient-apple-mesh'),

    # Text colors
    ('text-cream', 'text-white'),
    ('text-clay', 'text-apple-text-tertiary'),
    ('text-moss', 'text-apple-blue-600'),
    ('text-sage', 'text-apple-text-secondary'),
    ('text-charcoal', 'text-apple-text-primary'),
    ('text-terracotta', 'text-red-500'),

    # Border colors
    ('border-cream', 'border-white'),
    ('border-clay', 'border-apple-border-light'),
    ('border-moss', 'border-apple-blue-600'),
    ('border-sage', 'border-apple-border'),
    ('border-charcoal', 'border-apple-text-primary'),
    ('border-terracotta', 'border-red-500'),

    # Hover states
    ('hover:bg-moss', 'hover:bg-apple-blue-700'),
    ('hover:bg-sage', 'hover:bg-apple-blue-200'),
    ('hover:bg-clay', 'hover:bg-apple-bg-secondary'),
    ('hover:text-moss', 'hover:text-apple-blue-700'),
    ('hover:text-sage', 'hover:text-apple-blue-600'),
    ('hover:text-charcoal', 'hover:text-apple-text-primary'),
    ('hover:text-cream', 'hover:text-white'),
    ('hover:border-moss', 'hover:border-apple-blue-700'),

    # Focus states
    ('focus:border-moss', 'focus:border-apple-blue-600'),
]

def replace_colors_in_file(filepath):
    """Replace old color classes with Apple design system colors in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Apply all replacements
        for old, new in replacements:
            content = content.replace(old, new)

        # Only write if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Updated: {filepath.split('frontend')[-1]}")
            return True
        else:
            print(f"  No changes needed: {filepath.split('frontend')[-1]}")
            return False

    except Exception as e:
        print(f"[ERROR] Error updating {filepath}: {e}")
        return False

def main():
    print("Replacing old colors with Apple design system...")
    print()

    updated_count = 0
    for filepath in files_to_update:
        if replace_colors_in_file(filepath):
            updated_count += 1

    print()
    print(f"Color replacement complete! Updated {updated_count} file(s).")

if __name__ == '__main__':
    main()
