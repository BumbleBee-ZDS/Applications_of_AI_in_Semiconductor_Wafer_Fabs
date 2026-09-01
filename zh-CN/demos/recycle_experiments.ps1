Add-Type -AssemblyName Microsoft.VisualBasic

# Resolve project root at runtime to avoid non-ASCII chars in this script file
$root = (Get-ChildItem -LiteralPath 'H:\code\traework' -Directory | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'experiments') } | Select-Object -First 1).FullName
if (-not $root) { Write-Output 'ROOT NOT FOUND'; exit 1 }
$exp = Join-Path $root 'experiments'
Write-Output ('ROOT: ' + $root)

$unselected = @(
    'dissipative_structure_theory_agent',
    'engineer profile',
    'fab_memory_agent',
    'fab_ontology_yed_mvp',
    'fab_post_training_agent',
    'fab_report_llm_fine_tuning',
    'fab_sql_rag',
    'fab_text2sql'
)

$targets = @()
foreach ($u in $unselected) { $targets += Join-Path $exp $u }
$targets += Join-Path $exp 'FabCapacityAgent\fab_capacity_agent\data\fab_capacity.db'
$targets += Join-Path $exp 'fab_llm_fine_tuning\.venv'
$targets += Join-Path $exp 'fab_llm_fine_tuning\Qwen2-0.5B'
$targets += Join-Path $exp 'fab_llm_fine_tuning\fab_mvp\outputs\lora_adapter'

foreach ($t in $targets) {
    if (Test-Path -LiteralPath $t) {
        try {
            $item = Get-Item -LiteralPath $t
            if ($item.PSIsContainer) {
                [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($t, 'OnlyErrorDialogs', 'SendToRecycleBin')
            } else {
                [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($t, 'OnlyErrorDialogs', 'SendToRecycleBin')
            }
            Write-Output ('RECYCLED: ' + $t)
        } catch {
            Write-Output ('FAILED: ' + $t + ' - ' + $_.Exception.Message)
        }
    } else {
        Write-Output ('NOT FOUND: ' + $t)
    }
}
