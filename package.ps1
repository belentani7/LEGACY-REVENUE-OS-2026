param(
    [string]$Output = "..\LEGACY-REVENUE-OS-2026.zip"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path $PSScriptRoot).Path
$outputPath = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $Output))
$excludedSegments = @("\.git\", "\.venv\", "\__pycache__\", "\.pytest_cache\", "\artifacts\")
$excludedFiles = @(".env", "revenue.json")

$files = Get-ChildItem -LiteralPath $projectRoot -File -Recurse | Where-Object {
    $full = $_.FullName
    $relative = [System.IO.Path]::GetRelativePath($projectRoot, $full)
    $blockedSegment = $false
    foreach ($segment in $excludedSegments) {
        if (("\" + $relative + "\") -like ("*" + $segment + "*")) {
            $blockedSegment = $true
            break
        }
    }
    -not $blockedSegment -and
    $_.Name -notin $excludedFiles -and
    -not ($relative -like "pilots\*" -and $_.Name -ne ".gitkeep") -and
    $full -ne $outputPath
}

if (Test-Path -LiteralPath $outputPath) {
    Remove-Item -LiteralPath $outputPath -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::Open($outputPath, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($file in $files) {
        $relative = [System.IO.Path]::GetRelativePath($projectRoot, $file.FullName).Replace("\", "/")
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $archive,
            $file.FullName,
            "LEGACY-REVENUE-OS-2026/$relative",
            [System.IO.Compression.CompressionLevel]::Optimal
        ) | Out-Null
    }
}
finally {
    $archive.Dispose()
}

$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $outputPath).Hash.ToLowerInvariant()
[pscustomobject]@{
    Zip = $outputPath
    Files = $files.Count
    Bytes = (Get-Item -LiteralPath $outputPath).Length
    SHA256 = $hash
}
