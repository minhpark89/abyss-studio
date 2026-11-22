Option Explicit
Dim fs, shell, folder, command
Set fs = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
folder = fs.GetParentFolderName(WScript.ScriptFullName)
command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File " & Chr(34) & folder & "\Open-Muse-API.ps1" & Chr(34)
shell.Run command, 0, False
