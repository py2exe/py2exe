$testfailed = 0

Get-Content .\enabled_tests.txt | ForEach-Object {
    $testname = $_

    Write-Host "Running $testname..."
    cd $testname
    if (Test-Path -path .\requirements.txt -PathType Leaf) {
        pip install -r requirements.txt
    }
    python freeze.py
    cd dist

    if ($testname.Substring(0, 1) -eq '_') {
        $testexe = $testname.Substring(1)
    } else {
        $testexe = $testname
    }

    & ".\$testexe.exe"
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

