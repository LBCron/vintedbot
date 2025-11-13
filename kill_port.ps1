$port = 8000
$connection = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue

if ($connection) {
    $processId = $connection.OwningProcess
    Write-Host "Found process $processId on port $port"

    # Try to stop the process
    try {
        Stop-Process -Id $processId -Force -ErrorAction Stop
        Write-Host "Process $processId terminated successfully"
    }
    catch {
        Write-Host "Failed to stop process: $_"
        Write-Host "Process might be a zombie/orphaned socket"

        # Try using WMI
        try {
            $proc = Get-WmiObject Win32_Process -Filter "ProcessId=$processId"
            if ($proc) {
                $proc.Terminate()
                Write-Host "Process terminated via WMI"
            } else {
                Write-Host "Process not found in WMI - this is an orphaned TCP socket"
                Write-Host "This requires a system restart or specialized tools to clear"
            }
        }
        catch {
            Write-Host "WMI termination failed: $_"
        }
    }
} else {
    Write-Host "No process found listening on port $port"
}
