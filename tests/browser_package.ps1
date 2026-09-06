$ErrorActionPreference='Stop'
$env:PLAYWRIGHT_BROWSERS_PATH="$PSScriptRoot\..\.runtime\browsers"
$env:PLAYWRIGHT_MODULE='C:\Users\andy\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright'
$browserNode='C:\Users\andy\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
foreach ($appName in @('probe-a','probe-b','mosaic','error-interaction')) {
    $infoFile="artifacts/c04-$appName.json"
    if ($appName -like 'probe-*') {
        $output=wsl -d ubuntu-20.04 -u root -- unshare --mount --fork sh tests/browser_isolated.sh $appName
    } elseif ($appName -eq 'mosaic') {
        $output=wsl -d ubuntu-20.04 -- python3 dev/emu start --fixture mosaic
    } else {
        $output=wsl -d ubuntu-20.04 -- python3 dev/emu start --script fixtures/faults/error-interaction/error-interaction.lua --code-root fixtures/faults
    }
    if ($LASTEXITCODE -ne 0) {throw "Native startup failed: $appName"}
    $output | Set-Content $infoFile -Encoding utf8
    $sessionInfo=$output | ConvertFrom-Json
    try {
        if ($appName -like 'probe-*') { & $browserNode tests/browser_native.cjs $infoFile }
        else { & $browserNode tests/browser_application.cjs $infoFile }
        if ($LASTEXITCODE -ne 0) {throw "Browser package failed: $appName"}
    } finally {
        wsl -d ubuntu-20.04 -- python3 dev/emu stop $sessionInfo.session_id
        if ($LASTEXITCODE -ne 0) {throw "Native cleanup failed: $appName"}
        $sourceDirectory=".runtime/sessions/$($sessionInfo.session_id)"
        $targetDirectory="artifacts/c04/$appName/$($sessionInfo.session_id)"
        New-Item -ItemType Directory -Force -Path $targetDirectory | Out-Null
        Get-ChildItem -LiteralPath $sourceDirectory -File | Where-Object { $_.Extension -in @('.log','.jsonl') -or $_.Name -in @('cleanup.json','frame.bgra','native-config.json') } | Copy-Item -Destination $targetDirectory
    }
    wsl -d ubuntu-20.04 -- python3 tests/record_browser.py $appName $infoFile
    if ($LASTEXITCODE -ne 0) {throw "Browser evidence failed: $appName"}
}
