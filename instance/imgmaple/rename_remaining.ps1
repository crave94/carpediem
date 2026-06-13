$destFolder = "D:\imgmaple"

$mapping = @{
    "adele_maplestory.webp"                  = "adele.webp"
    "battle_mage_skill_build_guide.webp"     = "battle_mage.webp"
    "bishop_skill_guide.webp"                = "bishop.webp"
    "demon_avenger_skill_build_guide.webp"   = "demon_avenger.webp"
    "explorer_warrior_dark_knight.webp"      = "dark_knight.webp"
    "hero_explorer_warrior.webp"             = "hero.webp"
    "shadower_skill_build.webp"              = "shadower.webp"
    "maplestory_kanna_guide.webp"            = "kanna.webp"
    "maplestory_wild_hunter_remastered.webp" = "wild_hunter.webp"
    "maplestory_zero.webp"                   = "zero.webp"
}

foreach ($pair in $mapping.GetEnumerator()) {
    $src = Join-Path $destFolder $pair.Key
    $dst = Join-Path $destFolder $pair.Value
    if (Test-Path -LiteralPath $src) {
        if (Test-Path -LiteralPath $dst) {
            Write-Host "  SKIP (target exists): $($pair.Key)" -ForegroundColor Yellow
        } else {
            Rename-Item -LiteralPath $src -NewName $pair.Value
            Write-Host "  $($pair.Key) -> $($pair.Value)" -ForegroundColor Green
        }
    } else {
        Write-Host "  NOT FOUND: $($pair.Key)" -ForegroundColor Red
    }
}
