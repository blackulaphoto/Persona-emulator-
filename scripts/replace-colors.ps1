# PowerShell script to replace old color classes with Apple design system colors

$personaDetailPage = "E:\google photos\personality2\persona-evolution-simulator-complete\persona-evolution-simulator\frontend\app\persona\[id]\page.tsx"
$chatBoxPage = "E:\google photos\personality2\persona-evolution-simulator-complete\persona-evolution-simulator\frontend\app\persona\[id]\ChatBox.tsx"

# Define replacement pairs
$replacements = @(
    # Background colors
    @{Old='bg-cream'; New='bg-white'},
    @{Old='bg-clay'; New='bg-apple-bg-tertiary'},
    @{Old='bg-moss(?!/)'; New='bg-apple-blue-600'},
    @{Old='bg-sage'; New='bg-apple-blue-100'},
    @{Old='bg-charcoal(?!/)'; New='bg-apple-bg-primary'},
    @{Old='bg-terracotta'; New='bg-red-500'},
    @{Old='bg-grain'; New='bg-apple-bg-tertiary gradient-apple-mesh'},

    # Text colors
    @{Old='text-cream'; New='text-white'},
    @{Old='text-clay'; New='text-apple-text-tertiary'},
    @{Old='text-moss'; New='text-apple-blue-600'},
    @{Old='text-sage'; New='text-apple-text-secondary'},
    @{Old='text-charcoal'; New='text-apple-text-primary'},
    @{Old='text-terracotta'; New='text-red-500'},

    # Border colors
    @{Old='border-cream'; New='border-white'},
    @{Old='border-clay'; New='border-apple-border-light'},
    @{Old='border-moss(?!/)'; New='border-apple-blue-600'},
    @{Old='border-sage'; New='border-apple-border'},
    @{Old='border-charcoal/10'; New='border-apple-border-light'},
    @{Old='border-charcoal/20'; New='border-apple-border'},
    @{Old='border-charcoal(?!/)'; New='border-apple-text-primary'},
    @{Old='border-terracotta'; New='border-red-500'},

    # Hover states
    @{Old='hover:bg-moss'; New='hover:bg-apple-blue-700'},
    @{Old='hover:bg-sage'; New='hover:bg-apple-blue-200'},
    @{Old='hover:bg-clay'; New='hover:bg-apple-bg-secondary'},
    @{Old='hover:text-moss'; New='hover:text-apple-blue-700'},
    @{Old='hover:text-sage'; New='hover:text-apple-blue-600'},
    @{Old='hover:text-charcoal'; New='hover:text-apple-text-primary'},
    @{Old='hover:text-cream'; New='hover:text-white'},
    @{Old='hover:border-moss/30'; New='hover:border-apple-blue-200'},
    @{Old='hover:border-moss'; New='hover:border-apple-blue-700'},

    # Special opacity variants
    @{Old='bg-cream/80'; New='bg-white/80'},
    @{Old='bg-cream/70'; New='bg-white/70'},
    @{Old='bg-clay/20'; New='bg-apple-bg-tertiary/20'},
    @{Old='border-moss/30'; New='border-apple-blue-200'},

    # Focus states
    @{Old='focus:border-moss'; New='focus:border-apple-blue-600'}
)

# Apply replacements to persona detail page
$content = Get-Content $personaDetailPage -Raw

foreach ($pair in $replacements) {
    $content = $content -replace $pair.Old, $pair.New
}

Set-Content $personaDetailPage -Value $content

# Apply replacements to chat box
$content = Get-Content $chatBoxPage -Raw

foreach ($pair in $replacements) {
    $content = $content -replace $pair.Old, $pair.New
}

Set-Content $chatBoxPage -Value $content

Write-Host "✓ Color replacements complete!" -ForegroundColor Green
Write-Host "  - Updated: persona/[id]/page.tsx"
Write-Host "  - Updated: persona/[id]/ChatBox.tsx"
