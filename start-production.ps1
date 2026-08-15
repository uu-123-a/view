$ErrorActionPreference = "Stop"
$project = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $project
npm.cmd run build
$env:MOSS_ENV = "production"
$env:MOSS_COOKIE_SECURE = "false"
python -m waitress --host=127.0.0.1 --port=8000 --call server.app:create_app
