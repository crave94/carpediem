$ErrorActionPreference = "Continue"
$destFolder = "D:\imgmaple"
$baseUrl = "https://www.digitaltq.com"

if (-not (Test-Path -LiteralPath $destFolder)) {
    New-Item -ItemType Directory -Path $destFolder | Out-Null
}

Write-Host "Fetching main classes page..." -ForegroundColor Cyan
$mainPage = Invoke-WebRequest -Uri "$baseUrl/maplestory-classes-jobs" -UseBasicParsing
$html = $mainPage.Content

$linkPattern = 'href="(https://www\.digitaltq\.com/maplestory-[a-z0-9\-]+-skill-build[^"]*)"'
$rawMatches = [regex]::Matches($html, $linkPattern)
$urls = @()
foreach ($m in $rawMatches) {
    $u = $m.Groups[1].Value
    if ($urls -notcontains $u) { $urls += $u }
}

Write-Host "Found $($urls.Count) class pages." -ForegroundColor Green

$results = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
$scriptBlock = {
    param($u, $dest)
    try {
        $page = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 30
        $ogPattern = '<meta\s+property="og:image"\s+content="([^"]+)"'
        $og = [regex]::Match($page.Content, $ogPattern)
        if ($og.Success) {
            $img = $og.Groups[1].Value
            $name = [System.IO.Path]::GetFileName($img)
            $out = Join-Path $dest $name
            Invoke-WebRequest -Uri $img -OutFile $out -TimeoutSec 30 | Out-Null
            return [pscustomobject]@{ Url = $u; Image = $img; File = $out; Status = "OK" }
        } else {
            return [pscustomobject]@{ Url = $u; Image = ""; File = ""; Status = "No og:image" }
        }
    } catch {
        return [pscustomobject]@{ Url = $u; Image = ""; File = ""; Status = "Error: $_" }
    }
}

$throttle = 6
$jobs = @()
$completed = 0
$total = $urls.Count

foreach ($u in $urls) {
    while ((Get-Job -State Running).Count -ge $throttle) {
        Start-Sleep -Milliseconds 200
    }
    $jobs += Start-Job -ScriptBlock $scriptBlock -ArgumentList $u, $destFolder
}

Write-Host "Downloading images (parallel jobs)..." -ForegroundColor Cyan
foreach ($j in $jobs) {
    $r = Wait-Job $j | Receive-Job
    $completed++
    if ($r) {
        Write-Host "[$completed/$total] $($r.Status) - $($r.File)" -ForegroundColor $(if($r.Status -eq 'OK'){'Green'}else{'Yellow'})
    }
    Remove-Job $j -Force
}

Write-Host "`nDone. Files saved to $destFolder" -ForegroundColor Cyan
Get-ChildItem -LiteralPath $destFolder -File | Where-Object { $_.Name -like "maplestory-*" } | Select-Object Name, Length | Format-Table
