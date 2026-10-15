$os = Get-CimInstance Win32_OperatingSystem
$totalMB = [math]::Round($os.TotalVisibleMemorySize / 1024)
$freeMB = [math]::Round($os.FreePhysicalMemory / 1024)
$usedMB = $totalMB - $freeMB
$pct = [math]::Round(($usedMB / $totalMB) * 100)

Write-Host "=========================================="
Write-Host "  MEMORIA RAM"
Write-Host "=========================================="
Write-Host ("Total:  {0} MB" -f $totalMB)
Write-Host ("Livre:  {0} MB" -f $freeMB)
Write-Host ("Usado:  {0} MB ({1}%)" -f $usedMB, $pct)
Write-Host "=========================================="

# Top 10 processos por memória
Write-Host ""
Write-Host "TOP 10 PROCESSOS POR MEMORIA:"
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10 Id, ProcessName, @{Name="RAM (MB)"; Expression={[math]::Round($_.WorkingSet/1MB)}} | Format-Table -AutoSize