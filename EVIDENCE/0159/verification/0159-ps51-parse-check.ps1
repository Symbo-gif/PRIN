# PS 5.1 parse check of the AGENTS.md supervised-validation PowerShell
# example and the existing ruff --config gate line. Scratch tool only.
$ErrorActionPreference = 'Stop'
"PSVersion: $($PSVersionTable.PSVersion)"
$root = 'C:\dev\PRIN'
$lines = (Get-Content -Raw (Join-Path $root 'AGENTS.md')) -split "`r?`n"

$exampleLine = $lines | Where-Object { $_ -like '$previousPath=$env:PATH;*' }
$configLine  = $lines | Where-Object { $_ -like '*--config "include = *' }
"example_lines=$($exampleLine.Count) config_lines=$($configLine.Count)"

$errs1 = $null
[void][System.Management.Automation.PSParser]::Tokenize(($exampleLine -join "`n"), [ref]$errs1)
"example_parse_errors=$($errs1.Count)"

$errs2 = $null
[void][System.Management.Automation.PSParser]::Tokenize(($configLine -join "`n"), [ref]$errs2)
"config_parse_errors=$($errs2.Count)"

# Harmless stub execution of the same try/finally PATH-wrapper shape
# (no pytest run — executable stubbed to cmd echo).
$before = $env:PATH
$previousPath=$env:PATH; try { $env:PATH='C:\Program Files\Git\bin;'+$previousPath; & cmd /c "echo STUB-RAN"; $pytestExit=$LASTEXITCODE } finally { $env:PATH=$previousPath }
"stub_exit=$pytestExit path_restored=$($env:PATH -eq $before)"
