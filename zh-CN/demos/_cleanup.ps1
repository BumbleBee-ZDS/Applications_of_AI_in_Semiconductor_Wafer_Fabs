Add-Type -AssemblyName Microsoft.VisualBasic
$t = (Get-ChildItem -LiteralPath 'H:\code\traework' -Directory | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'experiments') } | Select-Object -First 1).FullName
$p = Join-Path $t 'zh-CN\demos\_check_git_status.py'
if (Test-Path -LiteralPath $p) {
    [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($p, 'OnlyErrorDialogs', 'SendToRecycleBin')
    Write-Output 'temp script recycled'
}
