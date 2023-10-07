$testfailed = 0

if ($args[0]) {
    $teststoexecute = ,$args[0]
} else {
    $teststoexecute = Get-Content .\enabled_tests.txt
}

$teststoexecute | ForEach-Object {
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

    ForEach ($executablename in Get-ChildItem -path "." -name -file | Where-Object {$_ -match "^$testexe(_[0-9])?\.exe$"}) {
        & ".\$executablename"
        $testfailed = $LastExitcode
        if ($executablename.TrimEnd(".exe") -eq $testname) {
            Write-Host "$testname exited with $testfailed"
        } else {
            Write-Host "Executable $executablename  for test $testname exited with $testfailed"
        }
        if ($testfailed -ne 0 ) {
            break
        }
    }
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

