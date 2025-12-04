@echo off
echo Killing processes on ports 8000-8003...

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /PID %%a /F 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8001" ^| findstr "LISTENING"') do taskkill /PID %%a /F 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8002" ^| findstr "LISTENING"') do taskkill /PID %%a /F 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8003" ^| findstr "LISTENING"') do taskkill /PID %%a /F 2>nul

echo Waiting 3 seconds...
timeout /t 3 /nobreak > nul

echo Starting employee-agent on port 8000...
start /b cmd /c "cd /d E:\Ailigent\employee-agent && employeeEnv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo Starting contracts-agent on port 8001...
start /b cmd /c "cd /d E:\Ailigent\contracts-agent && contractEnv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"

echo Starting hr-agent on port 8002...
start /b cmd /c "cd /d E:\Ailigent\hr-agent && hrEnv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload"

echo Starting task-management on port 8003...
start /b cmd /c "cd /d E:\Ailigent\task-management && taskMangEnv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload"

echo All services started with --reload flag!
timeout /t 5 /nobreak > nul
echo Testing health endpoints...
curl -s http://localhost:8000/health
echo.
curl -s http://localhost:8001/api/v1/health
echo.
curl -s http://localhost:8002/api/v1/health
echo.
curl -s http://localhost:8003/api/v1/health
echo.
echo Done!
