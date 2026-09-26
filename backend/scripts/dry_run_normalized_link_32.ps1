param(
    [string]$ApiBase = 'http://127.0.0.1:18000',
    [string]$Snapshot = 'backend/.tenderproof/product-completion/delivery-current-20260912T195125613173Z.json',
    [string]$AccessFile = 'backend/.tenderproof/local-pilot/ACESSO-LOCAL.md'
)
$ErrorActionPreference = 'Stop'

$snapshotData = Get-Content -Raw -LiteralPath $Snapshot | ConvertFrom-Json
$ids = @($snapshotData.catalogue | ForEach-Object { [int]$_.id })
if ($ids.Count -ne 32 -or ($ids | Sort-Object -Unique).Count -ne 32) { throw 'Snapshot não contém exatamente 32 IDs únicos' }

$access = Get-Content -Raw -LiteralPath $AccessFile
$email = [regex]::Match($access, '(?m)^E-mail:\s*(.+)$').Groups[1].Value.Trim()
$password = [regex]::Match($access, '(?m)^Senha:\s*(.+)$').Groups[1].Value.Trim()
$login = Invoke-RestMethod -Method Post -Uri "$ApiBase/auth/login" -ContentType 'application/json' -Body (@{ email = $email; password = $password } | ConvertTo-Json)
$headers = @{ Authorization = "Bearer $($login.access_token)" }
$authHash = (Get-FileHash -Algorithm SHA256 -LiteralPath 'docs/execucao/QUADRO.md').Hash.ToLowerInvariant()
$authorization = @{ actor_kind = 'delegated_automation'; human_read = $false; delegation_reference = 'T007-normalized-link-dry-run'; delegation_sha256 = $authHash }
$payload = @{ concurso_ids = $ids; authorization = $authorization } | ConvertTo-Json -Depth 8
$proposal = Invoke-RestMethod -Method Post -Uri "$ApiBase/tenderproof/publications/normalized-link/proposals" -Headers $headers -ContentType 'application/json' -Body $payload

$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$receiptPath = "backend/.tenderproof/product-completion/normalized-link-dry-run-$stamp.json"
$receipt = [ordered]@{
    kind = 'normalized_link_reference_dry_run'
    created_at = (Get-Date).ToUniversalTime().ToString('o')
    snapshot = (Resolve-Path $Snapshot).Path
    requested_ids = $ids
    proposal = $proposal
    credentials_used = $true
    paid_credentials_used = $false
    applied = $false
}
($receipt | ConvertTo-Json -Depth 12) | Set-Content -LiteralPath $receiptPath -Encoding UTF8
[ordered]@{ receipt = (Resolve-Path $receiptPath).Path; proposal_id = $proposal.id; proposal_hash = $proposal.proposal_hash; requested = $ids.Count; eligible = @($proposal.targets).Count; rejected = @($proposal.rejected_ids).Count; applied = $false } | ConvertTo-Json -Compress
