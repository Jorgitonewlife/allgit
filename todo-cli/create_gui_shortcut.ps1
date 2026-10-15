# Cria atalho do Todo GUI na Area de Trabalho
# Pode ser fixado na barra de tarefas (clique direito > Fixar na barra de tarefas)

$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Todo GUI.lnk"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "cmd.exe"
$Shortcut.Arguments = "/k todo-gui"
$Shortcut.WorkingDirectory = [Environment]::GetFolderPath("UserProfile")
$Shortcut.IconLocation = "C:\Users\Jorge A\AppData\Local\Programs\Python\Python312\Scripts\todo-gui.exe"
$Shortcut.Description = "Todo GUI - Interface Gráfica (PySide6)"
$Shortcut.Save()

Write-Host "Atalho criado: $ShortcutPath"
Write-Host "Clique com botao direito > 'Fixar na barra de tarefas' para adicionar a taskbar"