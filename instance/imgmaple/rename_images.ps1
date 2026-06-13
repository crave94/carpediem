$destFolder = "D:\imgmaple"

# Pattern: maplestory[-_]NAME[-_]skill[-_]build[-_]guide?.ext -> NAME.ext
$pattern = '^maplestory[-_](.+?)[-_]skill[-_]build(?:[-_]guide)?\.(webp|png|jpg|jpeg)$'

$renamed = @()
$skipped = @()
$collisions = @()

Get-ChildItem -LiteralPath $destFolder -File | ForEach-Object {
    if ($_.Name -match $pattern) {
        $newName = "$($Matches[1]).$($Matches[2])"
        $newPath = Join-Path $destFolder $newName
        if (Test-Path -LiteralPath $newPath) {
            $collisions += "$($_.Name) -> $newName (target exists)"
        } else {
            Rename-Item -LiteralPath $_.FullName -NewName $newName
            $renamed += "$($_.Name) -> $newName"
        }
    } else {
        $skipped += $_.Name
    }
}

Write-Host "`n=== RENAMED ($($renamed.Count)) ===" -ForegroundColor Green
$renamed | ForEach-Object { Write-Host "  $_" }

Write-Host "`n=== SKIPPED - no match ($($skipped.Count)) ===" -ForegroundColor Yellow
$skipped | ForEach-Object { Write-Host "  $_" }

if ($collisions.Count -gt 0) {
    Write-Host "`n=== COLLISIONS ===" -ForegroundColor Red
    $collisions | ForEach-Object { Write-Host "  $_" }
}
