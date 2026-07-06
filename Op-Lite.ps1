# Op-Lite.ps1 - no-admin-needed Pi-hole + DNS stack via Docker Desktop
$ErrorActionPreference = "Stop"
$Stack = "C:\Op\Op\stack"

function Log($m) {
  $ts = Get-Date -Format "HH:mm:ss"
  Write-Host "[$ts] $m" -ForegroundColor Cyan
}

# --- Ensure Docker Desktop is up (no admin needed for the service itself) ---
$docker = Get-Process com.docker.backend -ErrorAction SilentlyContinue
if (-not $docker) {
  Log "Starting Docker Desktop..."
  Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
  $docker = $null
  for ($i=0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 2
    try { docker info | Out-Null; if ($?) { break } } catch {}
  }
}
docker version | Out-Null
Log "Docker is up."

# --- Build the stack folder if missing ---
New-Item -ItemType Directory -Force -Path $Stack | Out-Null
New-Item -ItemType Directory -Force -Path "$Stack\etc-pihole" | Out-Null
New-Item -ItemType Directory -Force -Path "$Stack\etc-dnsmasq" | Out-Null

# --- docker-compose.yml (no Linux-only Unbound - keeps it Windows-friendly) ---
@"
services:
  pihole:
    container_name: pihole
    image: pihole/pihole:latest
    restart: unless-stopped
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      - "127.0.0.1:8080:80/tcp"
    environment:
      TZ: "America/New_York"
      WEBPASSWORD: "ChangeMe123!"
      DNS1: "1.1.1.1"
      DNS2: "9.9.9.9"
    volumes:
      - ./etc-pihole:/etc/pihole
      - ./etc-dnsmasq:/etc/dnsmasq.d
"@ | Set-Content -Encoding UTF8 "$Stack\docker-compose.yml"

# --- Start / restart the stack ---
Push-Location $Stack
docker compose down --remove-orphans 2>$null | Out-Null
docker compose up -d
Pop-Location

# --- Verify ---
Start-Sleep -Seconds 5
$running = (docker ps --filter "name=pihole" --format "{{.Names}}")
if ($running -match "pihole") {
  Log "Pi-hole is RUNNING on http://127.0.0.1:8080/admin"
} else {
  Log "Pi-hole failed to start. Logs:" -ForegroundColor Yellow
  docker logs pihole --tail 30
}

# --- Auto-set Windows DNS to point at itself (no admin needed for Set-DnsClientServerAddress per-interface on Ethernet) ---
$iface = Get-NetAdapter | Where-Object { $_.Status -eq "Up" -and $_.Name -notmatch "Loopback" } | Select-Object -First 1
if ($iface) {
  try {
    Log "Setting DNS on $($iface.Name) to 127.0.0.1"
    Set-DnsClientServerAddress -InterfaceAlias $iface.Name -ServerAddresses 127.0.0.1
  } catch {
    Log "Could not set DNS (admin needed): $_" -ForegroundColor Yellow
  }
}

Log "Done. Browser: http://127.0.0.1:8080/admin"