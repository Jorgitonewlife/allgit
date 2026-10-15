# Cria atalho do Todo CLI na Area de Trabalho
# Pode ser fixado na barra de tarefas (clique direito > Fixar na barra de tarefas)

$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Todo CLI.lnk"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "cmd.exe"
$Shortcut.Arguments = "/k todo"
$Shortcut.WorkingDirectory = [Environment]::GetFolderPath("UserProfile")
$Shortcut.IconLocation = "C:\Users\Jorge A\AppData\Local\Programs\Python\Python312\Scripts\todo.exe"
$Shortcut.Description = "Todo CLI - Gerenciador de tarefas"
$Shortcut.Save()

Write-Host "Atalho criado: $ShortcutPath"
Write-Host "Clique com botao direito > 'Fixar na barra de tarefas' para adicionar a taskbar"