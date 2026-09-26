param([ValidateSet('Start', 'Stop', 'Status', 'Backup', 'BuildWeb')][string]$Action = 'Status')
$ErrorActionPreference = 'Stop'
$pilotBackend = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../backend'))
$pilotMobile = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../mobile'))
function Invoke-PilotCompose {
    & docker compose --env-file "$pilotBackend/.env.pilot" -f "$pilotBackend/docker-compose.pilot.yml" @args
    if ($LASTEXITCODE -ne 0) { throw 'A operação Docker do piloto falhou.' }
}
if ($Action -eq 'Start') { Invoke-PilotCompose up -d; exit }
if ($Action -eq 'Stop') { Invoke-PilotCompose stop; exit }
if ($Action -eq 'Status') { Invoke-PilotCompose ps; exit }
if ($Action -eq 'BuildWeb') {
    $priorUrl = $env:EXPO_PUBLIC_API_BASE_URL
    $priorDotenv = $env:EXPO_NO_DOTENV
    Push-Location $pilotMobile
    try {
        $env:EXPO_PUBLIC_API_BASE_URL = '/api'
        $env:EXPO_NO_DOTENV = '1'
        & node node_modules/expo/bin/cli export --platform web --clear --output-dir dist-local-pilot
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao construir o aplicativo.' }
    } finally {
        Pop-Location
        $env:EXPO_PUBLIC_API_BASE_URL = $priorUrl
        $env:EXPO_NO_DOTENV = $priorDotenv
    }
    exit
}
if ($Action -eq 'Backup') {
    $pilotStamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
    $pilotBundle = "/backups/pilot-$pilotStamp"
    # Pause all writers; retain data and volumes. Backups are never overwritten.
    Invoke-PilotCompose stop -t 120 scheduler worker api
    try {
        Invoke-PilotCompose exec -T postgres pg_dump -U postgres -d observador -Fc -f "$pilotBundle-postgres.dump"
        Invoke-PilotCompose exec -T postgres pg_restore --list "$pilotBundle-postgres.dump" | Out-Null
        Invoke-PilotCompose run --rm --no-deps api python -m app.tenderproof.operational_backup backup /var/lib/observador/tenderproof "$pilotBundle-operational" --writers-stopped
        Invoke-PilotCompose run --rm --no-deps api python -m app.tenderproof.operational_backup verify "$pilotBundle-operational"
        Write-Output "Backup preservado no volume observador-pilot_pilot_backups: $pilotBundle"
    } finally {
        Invoke-PilotCompose up -d api worker scheduler
    }
}
