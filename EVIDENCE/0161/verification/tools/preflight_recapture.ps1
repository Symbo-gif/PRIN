# Re-capture (read-only) of the pre-flight facts AFTER leg 5, while the tracked tree is still clean.
# Labelled as a re-capture: the original pre-flight transcript is in log.md section 2.
Set-Location C:\dev\PRIN
$R = 'fae24c4393c7a0232e6c8f0a6388b1775aa5fc05'
$scratch = 'C:\Users\there\AppData\Local\Temp\claude\c--dev-PRIN\8a021180-4f6b-439e-9fe7-62b13011e219\scratchpad\e3'
$out = "$scratch\preflight-recapture.txt"
$hosted = "$scratch\hosted-runs-fae24c4.json"

function Section([string]$title, [scriptblock]$body) {
    "" | Out-File $out -Append -Encoding utf8
    "=== $title ===" | Out-File $out -Append -Encoding utf8
    & $body 2>&1 | Out-String | Out-File $out -Append -Encoding utf8
}

"RE-CAPTURE of the E3 pre-flight facts, taken after leg 5 and before any tracked file was edited." | Out-File $out -Encoding utf8
"The original pre-flight (2026-10-12T21:15Z-21:30Z) is transcribed in DOCS/experiments/EXP-002-.../log.md section 2." | Out-File $out -Append -Encoding utf8
"UTC-START: $((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))" | Out-File $out -Append -Encoding utf8
"HOST: $env:COMPUTERNAME  CWD: $(Get-Location)" | Out-File $out -Append -Encoding utf8

Section 'git rev-parse HEAD; git branch --show-current' { git rev-parse HEAD; git branch --show-current }
Section 'git status --porcelain=v1 --untracked-files=all  (expect only the E3 log and RUN- files)' { git status --porcelain=v1 --untracked-files=all; "exit=$LASTEXITCODE" }
Section 'git ls-files --others -- ":(glob)*.py" ":(glob)*.pth"  (expect empty)' { git ls-files --others -- ":(glob)*.py" ":(glob)*.pth"; "exit=$LASTEXITCODE" }
Section 'admission dry check (read-only), command exactly as in the session brief' {
    .venv\Scripts\python -I -c "import sys,json; sys.path.insert(0, r'C:\dev\PRIN'); from benchmarks.campaign import exp002_driver as d; print(json.dumps(d._admission('fae24c4393c7a0232e6c8f0a6388b1775aa5fc05'), sort_keys=True))"
    "exit=$LASTEXITCODE"
}
Section 'git diff --name-status 9a9889d fae24c4  (R against the approval commit)' { git diff --name-status 9a9889d fae24c4; "ancestor check:"; git merge-base --is-ancestor 9a9889d HEAD; "exit=$LASTEXITCODE" }
Section 'Host: OS / CPU / RAM' {
    Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, OSArchitecture, @{n = 'TotalVisibleMemoryMB'; e = { [math]::Round($_.TotalVisibleMemorySize / 1024) } }, @{n = 'FreePhysicalMemoryMB'; e = { [math]::Round($_.FreePhysicalMemory / 1024) } } | Format-List
    Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed | Format-List
    Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model, @{n = 'TotalPhysicalMemoryGiB'; e = { [math]::Round($_.TotalPhysicalMemory / 1GB, 2) } } | Format-List
}
Section 'Toolchain: python / rustc / cargo / nvidia-smi' {
    .venv\Scripts\python --version
    .venv\Scripts\python -I -c "import sys,platform,os; print(sys.executable); print(sys.version); print(platform.platform()); print(platform.processor()); print('cpu_count', os.cpu_count())"
    rustc --version
    cargo --version
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
}
Section 'Packages (importlib.metadata) and Matplotlib state' {
    .venv\Scripts\python -I -c "
import importlib.metadata as m
for p in ['matplotlib','numpy','pillow','prin-core','prinet','maturin','pytest','torch','fonttools','kiwisolver','contourpy','cycler','pyparsing','packaging','python-dateutil']:
    try: print(p, m.version(p))
    except Exception as e: print(p, 'NOT-INSTALLED')
import matplotlib, matplotlib.font_manager as fm, os, hashlib
print('mpl_cachedir', matplotlib.get_cachedir())
print('mpl_data_path', matplotlib.get_data_path())
p = os.path.join(matplotlib.get_cachedir(), 'fontlist-v%s.json' % fm.FontManager.__version__)
d = open(p,'rb').read()
print('fontcache', p, len(d), hashlib.sha256(d).hexdigest())
"
}
Section 'Installed extension (file facts only; nothing rebuilt)' {
    $e = Get-Item python\prin\_prin_core.pyd
    "{0}  {1} bytes  mtimeUtc={2}" -f (Get-FileHash $e.FullName -Algorithm SHA256).Hash.ToLower(), $e.Length, $e.LastWriteTimeUtc.ToString('o')
    "commits touching crates/ since 2026-09-28T00:00Z:"
    git log --since="2026-09-28T00:00:00Z" --format="%h %cI %s" -- crates Cargo.toml Cargo.lock
}
Section 'Pre-existing roots before the legs (from git): raw root tracked files' { git ls-files benchmarks/results/EXP-002 }

gh run list -R Symbo-gif/PRIN --commit $R --limit 50 --json databaseId,workflowName,event,status,conclusion,headSha,headBranch,createdAt,startedAt,updatedAt,attempt | Out-File $hosted -Encoding utf8
"" | Out-File $out -Append -Encoding utf8
"=== gh run list --commit $R  (saved verbatim as hosted-runs-fae24c4.json) ===" | Out-File $out -Append -Encoding utf8
"exit=$LASTEXITCODE; bytes=$((Get-Item $hosted).Length)" | Out-File $out -Append -Encoding utf8
"UTC-END: $((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))" | Out-File $out -Append -Encoding utf8
Get-Content $out
