#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Convert the self-hosted `PRIN-GPU-Runner` from an interactive process to an
    auto-start Windows service.

.DESCRIPTION
    ETCA-002 (DV-024 / DV-034): the runner has repeatedly gone offline because
    it was only ever started interactively (`run.cmd` in a terminal). It has no
    Windows service registered (`Get-Service actions.runner.*` returns nothing)
    and no `.service` file in C:\actions-runner, so it stops the moment the
    terminal closes, the user logs off, or the machine reboots or sleeps.

    This script removes the interactive registration and re-registers the runner
    as an auto-start service running as the interactive desktop user (so the
    Rust toolchain, CUDA, and the miniforge Python under C:\Users\there stay on
    PATH and the GPU stays accessible). It also disables AC-power sleep so the
    service stays reachable.

    Run it from an **elevated** PowerShell. `gh` must be authenticated
    (`gh auth status`). You will be prompted for the runner account's Windows
    password.

.NOTES
    After this runs once, the runner survives reboots with no manual step.
    Verify with:  Get-Service 'actions.runner.*'
                  gh api repos/Symbo-gif/PRIN/actions/runners --jq '.runners[].status'
#>

param(
    [string]$RunnerRoot = 'C:\actions-runner',
    [string]$Repo       = 'Symbo-gif/PRIN',
    [string]$RunnerName = 'PRIN-GPU-Runner',
    [string]$Labels     = 'gpu',
    # The account the service runs as. Default: the current interactive user, so
    # user-profile toolchains (rustup, miniforge, CUDA) resolve as they do today.
    [string]$Account    = "$env:USERDOMAIN\$env:USERNAME"
)

$ErrorActionPreference = 'Stop'
Set-Location $RunnerRoot

if (Test-Path "$RunnerRoot\.runner") {
    Write-Host "== Removing the existing runner registration =="
    $removeToken = (gh api -X POST "repos/$Repo/actions/runners/remove-token" --jq .token)
    # Don't abort if the server-side registration is already gone.
    try { & "$RunnerRoot\bin\Runner.Listener.exe" remove --token $removeToken }
    catch { Write-Warning "remove failed (already gone?) — continuing: $_" }
} else {
    Write-Host "== No local .runner config (runner already de-registered) — registering fresh =="
}

Write-Host "== Registering as an auto-start service (account: $Account) =="
$regToken = (gh api -X POST "repos/$Repo/actions/runners/registration-token" --jq .token)
& "$RunnerRoot\bin\Runner.Listener.exe" configure `
    --url "https://github.com/$Repo" `
    --token $regToken `
    --name $RunnerName `
    --labels $Labels `
    --unattended --replace `
    --runasservice `
    --windowslogonaccount $Account

Write-Host "== Disabling AC-power sleep / hibernate so the service stays online =="
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0

Write-Host "== Result =="
Get-Service 'actions.runner.*' | Format-Table Name, Status, StartType -AutoSize
Start-Service 'actions.runner.*' -ErrorAction SilentlyContinue
gh api "repos/$Repo/actions/runners" --jq '.runners[] | "\(.name): \(.status)"'
