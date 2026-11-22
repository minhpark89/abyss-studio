$ErrorActionPreference = 'Stop'
$studio = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$script = Join-Path $PSScriptRoot 'fieldnotes-daily.py'
$python = (& python -c "import sys; print(sys.executable)").Trim()
$pythonw = Join-Path (Split-Path $python) 'pythonw.exe'
if (!(Test-Path -LiteralPath $pythonw)) { throw 'Python for Windows is required.' }
$name = 'Abyss Fieldnotes Daily Analytics'
$existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if ($existing -and $existing.Actions.Arguments -notlike "*$script*") { throw 'Task name belongs to another command.' }
$action = New-ScheduledTaskAction -Execute $pythonw -Argument ('-X utf8 "' + $script + '"') -WorkingDirectory $studio
$trigger = New-ScheduledTaskTrigger -Daily -At '08:00'
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 20)
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
$info = Get-ScheduledTaskInfo -TaskName $name
$record = @{name=$name;time='08:00';zone=(Get-TimeZone).Id;nextAtInstall=$info.NextRunTime.ToString('o')}
$file = Join-Path $studio 'data\fieldnotes-schedule.json'
[IO.File]::WriteAllText($file, ($record | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
$info | Select-Object TaskName,NextRunTime
