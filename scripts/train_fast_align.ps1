param(
  [Parameter(Mandatory=$true)] [string]$FastAlign,
  [Parameter(Mandatory=$true)] [string]$ATools,
  [Parameter(Mandatory=$true)] [string]$ParallelCorpus
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $ParallelCorpus)) {
  throw "Parallel corpus not found: $ParallelCorpus"
}

$outDir = Split-Path -Parent $ParallelCorpus
$fwd = Join-Path $outDir "forward.align"
$rev = Join-Path $outDir "reverse.align"
$sym = Join-Path $outDir "sym.align"

& $FastAlign -i $ParallelCorpus -d -o -v *> $fwd
& $FastAlign -i $ParallelCorpus -d -o -v -r *> $rev
& $ATools -i $fwd -j $rev -c grow-diag-final-and *> $sym

Write-Host "Forward alignment: $fwd"
Write-Host "Reverse alignment: $rev"
Write-Host "Symmetrized alignment: $sym"
