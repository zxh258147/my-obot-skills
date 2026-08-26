# One-click PyPI publish for my-mcp-skill MCP packages.
# Examples:
#   .\publish.ps1
#   .\publish.ps1 --package card-verify-mcp
#   .\publish.ps1 --package weather-mcp --bump patch

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = $null
foreach ($candidate in @(
        (Join-Path $PSScriptRoot "card-verify-mcp\.venv\Scripts\python.exe"),
        (Join-Path $PSScriptRoot "weather-mcp\.venv\Scripts\python.exe"),
        "python"
    )) {
    if ($candidate -eq "python") {
        $python = "python"
        break
    }
    if (Test-Path $candidate) {
        $python = $candidate
        break
    }
}

& $python (Join-Path $PSScriptRoot "publish.py") @args
exit $LASTEXITCODE
