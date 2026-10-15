$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Docker WSL Fix.lnk"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "wsl.exe"
$Shortcut.Arguments = "bash /mnt/c/Users/Jorge A/Documents/Default Project/Opencode/todo-cli/docker-fix-wsl.sh"
$Shortcut.WorkingDirectory = [Environment]::GetFolderPath("UserProfile")
$Shortcut.IconLocation = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
$Shortcut.Description = "Fix Docker on WSL 2 - runs docker-fix-wsl.sh in WSL"
$Shortcut.Save()

Write-Host "Atalho criado: $ShortcutPath"
Write-Host "Clique com botao direito > 'Fixar na barra de tarefas' para adicionar a taskbar"