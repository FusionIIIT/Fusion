$Path = $PSScriptRoot
Get-ChildItem . -Include __pycache__,migrations -Recurse -Force | Remove-Item -Recurse -Force