# chrome-to-brave-bookmarks.ps1 - Migrate Chrome bookmarks to Brave
# Usage: Run in PowerShell (no admin needed)

$ErrorActionPreference = "Stop"

$CHROME_BOOKMARKS = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\AccountBookmarks"
$BRAVE_USER_DATA = "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\User Data"

$braveProfile = Get-ChildItem "$BRAVE_USER_DATA" -Directory | Where-Object { $_.Name -match '^(Default|Profile \d+)$' } | Select-Object -First 1
if (-not $braveProfile) {
    Write-Error "Brave profile not found. Open Brave once first."
    exit 1
}

$BRAVE_BOOKMARKS = Join-Path $braveProfile.FullName "Bookmarks"

Write-Host "=========================================="
Write-Host "  Chrome to Brave Bookmarks Migration"
Write-Host "=========================================="

if (-not (Test-Path $CHROME_BOOKMARKS)) {
    Write-Error "Chrome bookmarks not found: $CHROME_BOOKMARKS"
    exit 1
}
Write-Host "Chrome bookmarks found: $CHROME_BOOKMARKS"

if (-not (Test-Path $BRAVE_BOOKMARKS)) {
    Write-Error "Brave bookmarks not found: $BRAVE_BOOKMARKS. Open Brave once first."
    exit 1
}
Write-Host "Brave bookmarks found: $BRAVE_BOOKMARKS"

$backupPath = "$BRAVE_BOOKMARKS.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item $BRAVE_BOOKMARKS $backupPath -Force
Write-Host "Backup created: $backupPath"

$chromeJson = Get-Content $CHROME_BOOKMARKS -Raw | ConvertFrom-Json
$braveJson = Get-Content $BRAVE_BOOKMARKS -Raw | ConvertFrom-Json

# Debug: show structure
Write-Host "Debug: Chrome roots keys: $($chromeJson.roots.PSObject.Properties.Name -join ', ')"
foreach ($rn in $chromeJson.roots.PSObject.Properties.Name) {
    $r = $chromeJson.roots.$rn
    Write-Host ("  {0}: type={1}, children={2}" -f $rn, $r.type, $r.children.Count)
}

# Collect ALL bookmarks from Chrome (all roots)
function Get-AllBookmarks {
    param($node)
    $result = @()
    if ($node.type -eq 'url') {
        Write-Host "  Found URL: $($node.name) - $($node.url)"
        $result += [pscustomobject]@{
            name = $node.name
            url = $node.url
            date_added = $node.date_added
        }
    } elseif ($node.type -eq 'folder' -and $node.children) {
        Write-Host "  Entering folder: $($node.name) ($($node.children.Count) children)"
        foreach ($c in $node.children) {
            $result += Get-AllBookmarks -node $c
        }
    }
    return $result
}

$chromeBookmarks = @()
foreach ($rn in $chromeJson.roots.PSObject.Properties.Name) {
    $root = $chromeJson.roots.$rn
    if ($root.children) {
        foreach ($c in $root.children) {
            $chromeBookmarks += Get-AllBookmarks -node $c
        }
    }
}

Write-Host "Found $($chromeBookmarks.Count) Chrome bookmarks"

# Build existing URL set
$existingUrls = @{}
function Get-Urls($node) {
    if ($node.type -eq 'url') { $existingUrls[$node.url] = $true }
    elseif ($node.type -eq 'folder' -and $node.children) {
        foreach ($c in $node.children) { Get-Urls $c }
    }
}
foreach ($rn in $braveJson.roots.Keys) {
    foreach ($c in $braveJson.roots.$rn.children) { Get-Urls $c }
}

Write-Host "Existing Brave URLs: $($existingUrls.Count)"

$newBookmarks = $chromeBookmarks | Where-Object { -not $existingUrls.ContainsKey($_.url) }
Write-Host "New bookmarks to import: $($newBookmarks.Count)"

if ($newBookmarks.Count -eq 0) {
    Write-Host "No new bookmarks to import"
    exit 0
}

# Add to bookmark_bar
$added = 0
$bookmarkBar = $braveJson.roots.bookmark_bar
if (-not $bookmarkBar.children) { $bookmarkBar.children = @() }

foreach ($bm in $newBookmarks) {
    $exists = $bookmarkBar.children | Where-Object { $_.url -eq $bm.url }
    if (-not $exists) {
        $newBm = [pscustomobject]@{
            type = 'url'
            name = $bm.name
            url = $bm.url
            date_added = if ($bm.date_added) { $bm.date_added } else { [int]([DateTimeOffset]::UtcNow.ToUnixTimeSeconds() * 1000000 + 11644473600000000) }
        }
        $bookmarkBar.children += $newBm
        $added++
    }
}

Write-Host "Added $added bookmarks to bookmark_bar"

$braveJson | ConvertTo-Json -Depth 10 | Set-Content -Path $BRAVE_BOOKMARKS -Encoding UTF8
Write-Host "Import complete!"
Write-Host ""
Write-Host "=========================================="
Write-Host "Migration complete!"
Write-Host "=========================================="
Write-Host "1. Restart Brave"
Write-Host "2. Check Bookmarks bar (Ctrl+Shift+B)"
Write-Host "3. Backup at: $backupPath"