# Start the Insurance Insights Flask backend
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"
Set-Location "$PSScriptRoot\backend"
& ".\venv\Scripts\python.exe" app.py
