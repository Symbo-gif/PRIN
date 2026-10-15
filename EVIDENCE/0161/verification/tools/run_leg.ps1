# Launch ONE registered EXP-002 E3 leg exactly as protocol section 5.5 / e2-review.md section 8,
# capturing UTC start/end, exit code, wall time and the child's stdout/stderr outside the repository.
# This script writes only to the scratchpad directory and (through the driver) to the new RUN- root.
param(
    [Parameter(Mandatory = $true)][ValidateSet('api', 'conclusions', 'reference', 'prin', 'repeatability')][string]$Mode,
    [Parameter(Mandatory = $true)][string]$Label,
    [Parameter(Mandatory = $true)][string]$Tag
)

Set-Location C:\dev\PRIN
$R = 'fae24c4393c7a0232e6c8f0a6388b1775aa5fc05'
$R7 = $R.Substring(0, 7)
$scratch = 'C:\Users\there\AppData\Local\Temp\claude\c--dev-PRIN\8a021180-4f6b-439e-9fe7-62b13011e219\scratchpad\e3'

$utcStart = (Get-Date).ToUniversalTime()
$stamp = $utcStart.ToString('yyyyMMddTHHmmssZ')
$runId = "RUN-$stamp-$R7-$Label"
$runDir = "benchmarks/results/EXP-002/$runId"
$cmdText = ".venv\Scripts\python -m benchmarks.campaign.exp002_driver --mode $Mode --run-dir `"$runDir`" --operator MichaelMaillet --source-sha $R --seed-counter 0 --seed-key 2"

$meta = "$scratch\$Tag.meta.txt"
$out = "$scratch\$Tag.stdout.txt"
$err = "$scratch\$Tag.stderr.txt"
Remove-Item $meta, $out, $err -ErrorAction SilentlyContinue
"TAG=$Tag" | Out-File $meta -Encoding utf8
"MODE=$Mode" | Out-File $meta -Append -Encoding utf8
"RUN_ID=$runId" | Out-File $meta -Append -Encoding utf8
"COMMAND=$cmdText" | Out-File $meta -Append -Encoding utf8
"UTC_START=$($utcStart.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'))" | Out-File $meta -Append -Encoding utf8

$sw = [System.Diagnostics.Stopwatch]::StartNew()
& .venv\Scripts\python -m benchmarks.campaign.exp002_driver --mode $Mode --run-dir $runDir --operator MichaelMaillet --source-sha $R --seed-counter 0 --seed-key 2 > $out 2> $err
$exit = $LASTEXITCODE
$sw.Stop()
$utcEnd = (Get-Date).ToUniversalTime()

"UTC_END=$($utcEnd.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'))" | Out-File $meta -Append -Encoding utf8
"EXIT_CODE=$exit" | Out-File $meta -Append -Encoding utf8
"WALL_SECONDS=$([math]::Round($sw.Elapsed.TotalSeconds, 3))" | Out-File $meta -Append -Encoding utf8
"--- git status --porcelain=v1 --untracked-files=all (after the leg) ---" | Out-File $meta -Append -Encoding utf8
git status --porcelain=v1 --untracked-files=all 2>&1 | Out-File $meta -Append -Encoding utf8
"--- run directory entries ---" | Out-File $meta -Append -Encoding utf8
if (Test-Path "benchmarks\results\EXP-002\$runId") {
    Get-ChildItem "benchmarks\results\EXP-002\$runId" -Force | ForEach-Object { "{0}  {1} bytes" -f $_.Name, $_.Length } | Out-File $meta -Append -Encoding utf8
} else {
    "(run directory does not exist)" | Out-File $meta -Append -Encoding utf8
}
"DONE" | Out-File $meta -Append -Encoding utf8
Get-Content $meta
