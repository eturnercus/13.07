# PowerShell helper for Windows portable runtime download.
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Runtime = Join-Path $Root "runtime"
$Cache = Join-Path $Root ".cache"
New-Item -ItemType Directory -Force -Path $Cache | Out-Null

$TemurinUrl = "https://api.adoptium.net/v3/binary/latest/8/ga/windows/x64/jre/hotspot/normal/eclipse?project=jdk"
$ItwUrl = "https://github.com/AdoptOpenJDK/IcedTea-Web/releases/download/icedtea-web-1.8.8/icedtea-web-1.8.8.win.bin.zip"

function Download-File($Url, $Out) {
  if (Test-Path $Out) { return }
  Write-Host "Downloading $Url"
  Invoke-WebRequest -Uri $Url -OutFile $Out
}

$JreZip = Join-Path $Cache "temurin8-jre-windows.zip"
$ItwZip = Join-Path $Cache "icedtea-web-win.zip"
Download-File $TemurinUrl $JreZip
Download-File $ItwUrl $ItwZip

if (Test-Path $Runtime) { Remove-Item -Recurse -Force $Runtime }
New-Item -ItemType Directory -Force -Path $Runtime | Out-Null

Expand-Archive -Path $JreZip -DestinationPath (Join-Path $Cache "temurin-win") -Force
$JreSrc = Get-ChildItem (Join-Path $Cache "temurin-win") -Directory | Where-Object { $_.Name -like "jdk8u*-jre" } | Select-Object -First 1
Copy-Item -Recurse -Force (Join-Path $JreSrc.FullName "*") $Runtime

Expand-Archive -Path $ItwZip -DestinationPath (Join-Path $Cache "icedtea-win") -Force
$ItwSrc = Get-ChildItem (Join-Path $Cache "icedtea-win") -Directory | Where-Object { $_.Name -like "icedtea-web-*" } | Select-Object -First 1
Copy-Item -Recurse -Force (Join-Path $ItwSrc.FullName "*") (Join-Path $Runtime "icedtea-web")

@'
@echo off
setlocal
set "ROOT=%~dp0.."
set "JAVA_HOME=%ROOT%"
set "PATH=%ROOT%\bin;%PATH%"
"%ROOT%\icedtea-web\bin\javaws.exe" %*
'@ | Set-Content -Encoding ASCII (Join-Path $Runtime "bin\javaws.cmd")

Write-Host "Runtime installed to $Runtime"
