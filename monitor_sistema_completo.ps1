Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "Monitoramento Completo do Sistema"
$form.Size = New-Object System.Drawing.Size(700, 750)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedSingle"
$form.MaximizeBox = $false
$form.BackColor = [System.Drawing.Color]::FromArgb(240, 245, 250)

$tabControl = New-Object System.Windows.Forms.TabControl
$tabControl.Dock = "Fill"
$form.Controls.Add($tabControl) | Out-Null

# ABA 1: MEMORIA
$tabMemory = New-Object System.Windows.Forms.TabPage("Memoria RAM")
$tabMemory.BackColor = [System.Drawing.Color]::White
$tabControl.TabPages.Add($tabMemory) | Out-Null

$groupMem = New-Object System.Windows.Forms.GroupBox
$groupMem.Location = New-Object System.Drawing.Point(20, 20)
$groupMem.Size = New-Object System.Drawing.Size(660, 220)
$groupMem.Text = "Utilizacao de Memoria"
$groupMem.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)

$labelRamUsed = New-Object System.Windows.Forms.Label
$labelRamUsed.Location = New-Object System.Drawing.Point(20, 35)
$labelRamUsed.AutoSize = $true
$labelRamUsed.Font = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$labelRamUsed.ForeColor = [System.Drawing.Color]::DarkGreen

$labelRamTotal = New-Object System.Windows.Forms.Label
$labelRamTotal.Location = New-Object System.Drawing.Point(20, 70)
$labelRamTotal.AutoSize = $true
$labelRamTotal.Font = New-Object System.Drawing.Font("Segoe UI", 11)

$progressRam = New-Object System.Windows.Forms.ProgressBar
$progressRam.Location = New-Object System.Drawing.Point(20, 100)
$progressRam.Size = New-Object System.Drawing.Size(620, 35)
$progressRam.Style = "Continuous"
$progressRam.Minimum = 0
$progressRam.Maximum = 100

$labelRamDetail = New-Object System.Windows.Forms.Label
$labelRamDetail.Location = New-Object System.Drawing.Point(20, 150)
$labelRamDetail.AutoSize = $true
$labelRamDetail.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$labelRamDetail.ForeColor = [System.Drawing.Color]::Gray

$buttonCleanRam = New-Object System.Windows.Forms.Button
$buttonCleanRam.Location = New-Object System.Drawing.Point(20, 195)
$buttonCleanRam.Size = New-Object System.Drawing.Size(620, 45)
$buttonCleanRam.Text = "Limpar Memoria (Encerrar Top 5 Processos CPU)"
$buttonCleanRam.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
$buttonCleanRam.BackColor = [System.Drawing.Color]::LightGreen
$buttonCleanRam.Add_Click({
    $proc = Get-Process | Where-Object { $_.CPU -gt 0 } | Sort-Object CPU -Descending | Select-Object -First 5
    foreach ($p in $proc) {
        try { Stop-Process -Id $p.Id -ErrorAction Stop } catch {}
    }
    Update-RamDisplay
})

$groupMem.Controls.Add($labelRamUsed) | Out-Null
$groupMem.Controls.Add($labelRamTotal) | Out-Null
$groupMem.Controls.Add($progressRam) | Out-Null
$groupMem.Controls.Add($labelRamDetail) | Out-Null
$groupMem.Controls.Add($buttonCleanRam) | Out-Null

$tabMemory.Controls.Add($groupMem) | Out-Null

# ABA 2: CPU
$tabCpu = New-Object System.Windows.Forms.TabPage("Processador CPU")
$tabCpu.BackColor = [System.Drawing.Color]::White
$tabControl.TabPages.Add($tabCpu) | Out-Null

$groupCpu = New-Object System.Windows.Forms.GroupBox
$groupCpu.Location = New-Object System.Drawing.Point(20, 20)
$groupCpu.Size = New-Object System.Drawing.Size(660, 220)
$groupCpu.Text = "Utilizacao do Processador"
$groupCpu.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)

$labelCpuUsage = New-Object System.Windows.Forms.Label
$labelCpuUsage.Location = New-Object System.Drawing.Point(20, 35)
$labelCpuUsage.AutoSize = $true
$labelCpuUsage.Font = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$labelCpuUsage.ForeColor = [System.Drawing.Color]::DarkBlue

$progressCpu = New-Object System.Windows.Forms.ProgressBar
$progressCpu.Location = New-Object System.Drawing.Point(20, 80)
$progressCpu.Size = New-Object System.Drawing.Size(620, 35)
$progressCpu.Style = "Continuous"
$progressCpu.Minimum = 0
$progressCpu.Maximum = 100

$labelCpuDetail = New-Object System.Windows.Forms.Label
$labelCpuDetail.Location = New-Object System.Drawing.Point(20, 130)
$labelCpuDetail.AutoSize = $true
$labelCpuDetail.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$labelCpuDetail.ForeColor = [System.Drawing.Color]::Gray

$groupCpu.Controls.Add($labelCpuUsage) | Out-Null
$groupCpu.Controls.Add($progressCpu) | Out-Null
$groupCpu.Controls.Add($labelCpuDetail) | Out-Null

$tabCpu.Controls.Add($groupCpu) | Out-Null

# ABA 3: GPU
$tabGpu = New-Object System.Windows.Forms.TabPage("Placa Video GPU")
$tabGpu.BackColor = [System.Drawing.Color]::White
$tabControl.TabPages.Add($tabGpu) | Out-Null

$groupGpu = New-Object System.Windows.Forms.GroupBox
$groupGpu.Location = New-Object System.Drawing.Point(20, 20)
$groupGpu.Size = New-Object System.Drawing.Size(660, 220)
$groupGpu.Text = "Informacoes da Placa de Video"
$groupGpu.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)

$labelGpuInfo = New-Object System.Windows.Forms.Label
$labelGpuInfo.Location = New-Object System.Drawing.Point(20, 40)
$labelGpuInfo.AutoSize = $true
$labelGpuInfo.Font = New-Object System.Drawing.Font("Segoe UI", 12)
$labelGpuInfo.Text = "Carregando informacoes da GPU..."

$groupGpu.Controls.Add($labelGpuInfo) | Out-Null

$tabGpu.Controls.Add($groupGpu) | Out-Null

# ABA 4: TEMPERATURA
$tabTemp = New-Object System.Windows.Forms.TabPage("Temperatura")
$tabTemp.BackColor = [System.Drawing.Color]::White
$tabControl.TabPages.Add($tabTemp) | Out-Null

$groupTemp = New-Object System.Windows.Forms.GroupBox
$groupTemp.Location = New-Object System.Drawing.Point(20, 20)
$groupTemp.Size = New-Object System.Drawing.Size(660, 220)
$groupTemp.Text = "Temperatura do Sistema"
$groupTemp.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)

$labelTemperaturas = New-Object System.Windows.Forms.Label
$labelTemperaturas.Location = New-Object System.Drawing.Point(20, 40)
$labelTemperaturas.AutoSize = $true
$labelTemperaturas.Font = New-Object System.Drawing.Font("Segoe UI", 12)
$labelTemperaturas.Text = "Lendo dados de temperatura..."
$labelTemperaturas.ForeColor = [System.Drawing.Color]::DimGray

$groupTemp.Controls.Add($labelTemperaturas) | Out-Null

$tabTemp.Controls.Add($groupTemp) | Out-Null

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 2000

$timer.Add_Tick({
    Update-AllDisplay
})

$timer.Start()

function Update-RamDisplay {
    try {
        $proc = Get-Process | Select-Object @{Name="Mem";Expression={$_.WorkingSet64}},
                                     @{Name="ProcName";Expression={$_.ProcessName}}
        $totalMem = ([math]::Round((Get-CimInstance -ClassName Win32_ComputerSystem).TotalPhysicalMemory / 1MB))
        $usedMem = [math]::Round(($proc | Measure-Object -Property Mem -Sum).Sum / 1MB, 2)
        $pct = [math]::Round(($usedMem / $totalMem) * 100, 2)
        
        $labelRamUsed.Text = "Usada: $usedMem MB de $totalMem MB"
        $progressRam.Value = [int]$pct
        
        if ($pct -ge 80) { $progressRam.ForeColor = [System.Drawing.Color]::Red }
        elseif ($pct -ge 60) { $progressRam.ForeColor = [System.Drawing.Color]::Orange }
        else { $progressRam.ForeColor = [System.Drawing.Color]::Green }
        
        $labelRamDetail.Text = "Top 5 processos por CPU - Clique em 'Limpar' para encerrar"
$labelRamDetail.ForeColor = [System.Drawing.Color]::DarkGreen
    } catch {
        $labelRamUsed.Text = "Erro ao ler memoria"
        $progressRam.Value = 0
    }
}

function Update-CpuDisplay {
    try {
        $cpuPct = (Get-Counter "\Processor(_Total)\% Processor Time" -SampleInterval 1 -CounterSample 1).CounterSamples[0].CookedValue
        $labelCpuUsage.Text = "Uso: $([math]::Round($cpuPct, 2))%"
        $progressCpu.Value = [int]$cpuPct
        
        if ($cpuPct -ge 80) { $progressCpu.ForeColor = [System.Drawing.Color]::Red }
        elseif ($cpuPct -ge 60) { $progressCpu.ForeColor = [System.Drawing.Color]::Orange }
        else { $progressCpu.ForeColor = [System.Drawing.Color]::Blue }
        
        $labelCpuDetail.Text = "Atualizado: $(Get-Date -Format 'HH:mm:ss')"
$labelCpuDetail.ForeColor = [System.Drawing.Color]::Gray
    } catch {
        $labelCpuUsage.Text = "Erro ao ler CPU"
        $progressCpu.Value = 0
    }
}

function Update-GpuDisplay {
    try {
        $gpu = Get-CimInstance -Namespace "root\cimv2" -ClassName Win32_VideoController | Select-Object -First 1
        if ($gpu) {
            $name = $gpu.Name
            $mem = [math]::Round($gpu.AdapterRAM / 1MB, 2)
            $labelGpuInfo.Text = "GPU: $name`nMemoria: $mem MB"
        } else {
            $labelGpuInfo.Text = "Nenhuma GPU detectada"
        }
    } catch {
        $labelGpuInfo.Text = "Erro ao ler informacoes da GPU"
    }
}

function Update-TempDisplay {
    try {
        $cim = Get-CimInstance -Namespace "root/wmi" -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue
        $tempLines = @()
        if ($cim) {
            foreach ($t in $cim) {
                $degC = $t.Temperature / 10 - 273.15
                $tempLines += "$($t.DeviceID): $([math]::Round($degC, 1))C"
            }
        }
        if ($tempLines.Count -gt 0) {
            $labelTemperaturas.Text = "Temperaturas do Sistema:`n$($tempLines -join "`n")"
        } else {
            $labelTemperaturas.Text = "Leitura de temperatura nao disponivel neste hardware"
        }
    } catch {
        $labelTemperaturas.Text = "Erro ao ler temperatura"
    }
}

function Update-AllDisplay {
    Update-RamDisplay
    Update-CpuDisplay
    Update-GpuDisplay
    Update-TempDisplay
}

Update-AllDisplay

$form.ShowDialog() | Out-Null