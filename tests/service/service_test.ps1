$exitCode = 0

try {
    # Install dependencies
    Write-Host "Installing dependencies..."
    & python -m pip install -r "requirements.txt"
    if ($LASTEXITCODE -ne 0) {
        $exitCode = $LASTEXITCODE
        throw "Failed to install dependencies"
    }

    # Freeze service
    Write-Host "Freezing service..."
    & python "freeze.py"
    if ($LASTEXITCODE -ne 0) {
        $exitCode = $LASTEXITCODE
        throw "Failed to freeze service"
    }

    # Check executable exists
    if (-not (Test-Path -LiteralPath "dist\service_test.exe" -PathType Leaf)) {
        $exitCode = 1
        throw "Executable not found: dist\service_test.exe"
    }

    # Run service tests
    Write-Host "Running service install..."
    & "dist\service_test.exe" install
    if ($LASTEXITCODE -ne 0) {
        $exitCode = $LASTEXITCODE
        throw "Service install failed"
    }

    Write-Host "Running service start..."
    & "dist\service_test.exe" start
    if ($LASTEXITCODE -ne 0) {
        $exitCode = $LASTEXITCODE
        throw "Service start failed"
    }

    Start-Sleep -Seconds 2

    Write-Host "Running service stop..."
    & "dist\service_test.exe" stop
    if ($LASTEXITCODE -ne 0) {
        $exitCode = $LASTEXITCODE
        throw "Service stop failed"
    }

    Write-Host "Running service remove..."
    & "dist\service_test.exe" remove
    if ($LASTEXITCODE -ne 0) {
        $exitCode = $LASTEXITCODE
        throw "Service remove failed"
    }

    # Validate log
    if (-not (Test-Path -LiteralPath "dist\minimal_service.log" -PathType Leaf)) {
        $exitCode = 1
        throw "Log file not found: dist\minimal_service.log"
    }

    $logLines = Get-Content -LiteralPath "dist\minimal_service.log" | ForEach-Object { $_.Trim() }
    if ((-not ($logLines -contains "hello")) -or (-not ($logLines -contains "goodbye"))) {
        $exitCode = 1
        throw "Log validation failed"
    }

    Write-Host "Test passed"
}
catch {
    Write-Host "Test failed"
    Write-Host "Error: $_"
    if ($exitCode -eq 0) {
        $exitCode = 1
    }
}
finally {
    Write-Host "Removing test dependencies..."
    & python -m pip uninstall -r "requirements.txt" -y

    Write-Host "Removing dist folder..."
    & Remove-Item -LiteralPath "dist" -Force -Recurse
}

exit $exitCode
