# test_routing_api.ps1
# PowerShell script to test smart routing API

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "SMART ROUTING API TEST" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Test queries
$testCases = @(
    @{
        name     = "Outlook Query"
        message  = "My Outlook email is not syncing properly"
        expected = "rag_outlook"
        icon     = "📧"
    },
    @{
        name     = "Shopping Query"
        message  = "Find cheap laptops under $500"
        expected = "browser_use"
        icon     = "🌐"
    },
    @{
        name     = "General Query"
        message  = "What is the capital of France?"
        expected = "mistral"
        icon     = "🤖"
    },
    @{
        name     = "Flight Search"
        message  = "Find cheap flights to Paris"
        expected = "browser_use"
        icon     = "🌐"
    },
    @{
        name     = "Email Problem"
        message  = "Can't send emails from Outlook"
        expected = "rag_outlook"
        icon     = "📧"
    }
)

$baseUrl = "http://localhost:5000"
$successCount = 0
$failCount = 0

foreach ($test in $testCases) {
    Write-Host "`nTest: " -NoNewline
    Write-Host $test.name -ForegroundColor Cyan
    Write-Host "Query: " -NoNewline
    Write-Host $test.message -ForegroundColor White
    
    try {
        $body = @{message = $test.message } | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "$baseUrl/chat" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 5
        
        $route = $response.route
        $confidence = [math]::Round($response.confidence * 100)
        
        Write-Host "  → Route: " -NoNewline
        Write-Host "$($test.icon) $route" -ForegroundColor Green
        Write-Host "  → Confidence: " -NoNewline
        Write-Host "$confidence%" -ForegroundColor $(if ($confidence -ge 70) { "Green" } elseif ($confidence -ge 50) { "Yellow" } else { "Red" })
        Write-Host "  → Response: " -NoNewline -ForegroundColor Gray
        Write-Host $response.content -ForegroundColor Gray
        
        if ($route -eq $test.expected) {
            Write-Host "  ✓ PASS" -ForegroundColor Green
            $successCount++
        }
        else {
            Write-Host "  ✗ FAIL" -ForegroundColor Red -NoNewline
            Write-Host " (expected: $($test.expected))" -ForegroundColor Red
            $failCount++
        }
    }
    catch {
        Write-Host "  ✗ ERROR: " -NoNewline -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        $failCount++
    }
}

Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "TEST RESULTS" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Passed: " -NoNewline -ForegroundColor Green
Write-Host $successCount
Write-Host "Failed: " -NoNewline -ForegroundColor Red
Write-Host $failCount
Write-Host "Total:  " -NoNewline
Write-Host ($successCount + $failCount)

# Get routing statistics
try {
    Write-Host "`nRouting Statistics:" -ForegroundColor Cyan
    $stats = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    Write-Host "  Total routes: $($stats.routing_stats.total_routes)"
    Write-Host "  By destination:"
    foreach ($dest in $stats.routing_stats.by_destination.PSObject.Properties) {
        Write-Host "    - $($dest.Name): $($dest.Value)"
    }
    $avgConf = [math]::Round($stats.routing_stats.average_confidence * 100)
    Write-Host "  Average confidence: $avgConf%"
}
catch {
    Write-Host "Could not fetch statistics" -ForegroundColor Yellow
}

Write-Host ""
