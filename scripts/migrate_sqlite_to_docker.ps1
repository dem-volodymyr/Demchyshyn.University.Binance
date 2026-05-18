# Migrate data from local SQLite (db.sqlite3) into PostgreSQL running in Docker.
# Usage (from project root):
#   .\scripts\migrate_sqlite_to_docker.ps1
#   .\scripts\migrate_sqlite_to_docker.ps1 -SqlitePath "C:\path\to\db.sqlite3"
#   .\scripts\migrate_sqlite_to_docker.ps1 -ResetPostgres   # wipe Docker DB volume first

param(
    [string]$SqlitePath = "db.sqlite3",
    [string]$Fixture = "fixtures/sqlite_export.json",
    [switch]$ResetPostgres
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$SqliteFull = if ([System.IO.Path]::IsPathRooted($SqlitePath)) { $SqlitePath } else { Join-Path $ProjectRoot $SqlitePath }
if (-not (Test-Path $SqliteFull)) {
    Write-Error "SQLite file not found: $SqliteFull`nPlace your db.sqlite3 in the project root or pass -SqlitePath."
}

Write-Host "==> 1/4 Export from SQLite: $SqliteFull"
$env:DATABASE_URL = ""
$env:DJANGO_DB_NAME = ""
py -3 manage.py export_sqlite_fixture --sqlite $SqlitePath --output $Fixture
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($ResetPostgres) {
    Write-Host "==> Resetting Postgres volume (docker compose down -v)..."
    docker compose down -v
}

Write-Host "==> 2/4 Start Postgres and apply migrations"
docker compose up -d db
docker compose run --rm web python manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> 3/4 Load fixture into PostgreSQL"
docker compose run --rm web python manage.py loaddata $Fixture
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> 4/4 Start web service"
docker compose up -d web

Write-Host ""
Write-Host "Done. Open http://localhost:8000" -ForegroundColor Green
Write-Host "Fixture saved at: $Fixture"
