#!/usr/bin/env pwsh
param(
    [int]$topProcesses = 20,
    [switch]$force
)

Write-Host "=== LIMPAR MEMÓRIA RAM - WINDOWS ===" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

Write-Host "`nTop $topProcesses processos mais consumidores:`n" -ForegroundColor Yellow

$processes = Get-Process | Sort-Object -Property CPU -Descending | Select-Object -Top $topProcesses

$i = 1
foreach ($proc in $processes) {
    $memMB = [math]::Round($proc.WorkingSet64 / 1MB, 2)
    Write-Host "$i. Nome: $($proc.ProcessName) | Memória: $memMB MB | CPU: $($proc.CPU)s" -ForegroundColor White
    $i++
}

Write-Host "`nOpções:`n" -ForegroundColor Gray
Write-Host "  1. Finalizar processo selecionado" -ForegroundColor Gray
Write-Host "  2. Limpar processos do sistema comuns" -ForegroundColor Gray
Write-Host "  3. Sair" -ForegroundColor Gray

$input = Read-Host "Escolha uma opção (1-3)"

if ($input -eq '3' -or $input -eq 's' -or $input -eq 'S') {
    Write-Host "Saindo..." -ForegroundColor Green
    return
}

if ($input -eq '2') {
    Write-Host "`nLimpando processos do sistema comuns..." -ForegroundColor Yellow
    $systemProcesses = @("SearchIndexer", "WmiPrvse", "Svchost", "FontCache")
    foreach ($proc in $systemProcesses) {
        $found = Get-Process -Name $proc -ErrorAction SilentlyContinue
        if ($found) {
            Write-Host "Finalizando $proc (PID: $($found.Id))..." -ForegroundColor Cyan
            if ($force) {
                Stop-Process -Id $found.Id -Force
                Write-Host "  Finalizado FORÇADAMENTE!" -ForegroundColor Green
            } else {
                $confirm = Read-Host "Terminar $proc? (s/n)"
                if ($confirm -eq 's' -or $confirm -eq 'S') {
                    Stop-Process -Id $found.Id
                    Write-Host "  Finalizado!" -ForegroundColor Green
                } else {
                    Write-Host "  Pulo." -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "  $proc não está rodando." -ForegroundColor Gray
        }
    }
    Write-Host "`nLimpeza do sistema concluída!" -ForegroundColor Green
    return
}

if ($input -eq '1') {
    Write-Host "`nSelecione o número do processo a terminar:`n" -ForegroundColor Gray
    $input2 = Read-Host "Digite o número ou 's' para sair"
    
    if ($input2 -eq 's' -or $input2 -eq 'S') {
        Write-Host "Operação cancelada." -ForegroundColor Green
        return
    }
    
    try {
        $index = [int]$input2 - 1
        if ($index -ge 0 -and $index -lt $processes.Count) {
            $selected = $processes[$index]
            Write-Host "Processo selecionado: $($selected.ProcessName) (PID: $($selected.Id))" -ForegroundColor Yellow
            
            if ($force) {
                Stop-Process -Id $selected.Id -Force
                Write-Host "Processo finalizado FORÇADAMENTE!" -ForegroundColor Green
            } else {
                $confirm = Read-Host "Tem certeza? (s/n)"
                if ($confirm -eq 's' -or $confirm -eq 'S') {
                    Stop-Process -Id $selected.Id
                    Write-Host "Processo finalizado!" -ForegroundColor Green
                } else {
                    Write-Host "Operação cancelada." -ForegroundColor Green
                }
            }
        } else {
            Write-Host "Número inválido!" -ForegroundColor Red
        }
    } catch {
        Write-Host "Erro: $_" -ForegroundColor Red
    }
} else {
    Write-Host "Opção inválida!" -ForegroundColor Red
}