$testfailed = 0

Get-ChildItem -Recurse -Directory | ForEach-Object {
    $testname = $_.Name
    Write-Host "Running $testname..."
    cd $testname
    if (Test-Path -path .\requirements.txt -PathType Leaf) {
        pip install -r requirements.txt
    }
    python setup.py py2exe
    cd dist
    & ".\$testname.exe"
    $testfailed = $LastExitcode
    Write-Host "$testname exited with $testfailed"

    cd ..
    Remove-Item -LiteralPath "dist" -Force -Recurse
    if (Test-Path -path .\requirements.txt -PathType Leaf) {
        pip uninstall -r requirements.txt -y
    }
    cd ..

    if ($testfailed -ne 0) {
        Write-Host "$testname FAILED!!!"
        exit $testfailed
    }

    Write-Host "----------------- $testname PASS -------------------------"
}

