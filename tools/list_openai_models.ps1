param(
    [string]$BaseUrl = "",
    [string]$ApiKeyEnv = "ANTHROPIC_AUTH_TOKEN"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
    $BaseUrl = $env:AIHUB_OPENAI_BASE_URL
}
if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
    $BaseUrl = $env:OPENAI_BASE_URL
}
if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
    $BaseUrl = "http://aihub.lingrendev.com:8080"
}

$apiKey = [Environment]::GetEnvironmentVariable($ApiKeyEnv)
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    throw "missing API key environment variable: $ApiKeyEnv"
}

$normalized = $BaseUrl.TrimEnd("/")
if ($normalized.EndsWith("/v1")) {
    $endpoint = "$normalized/models"
} else {
    $endpoint = "$normalized/v1/models"
}

$headers = @{
    Authorization = "Bearer $apiKey"
    Accept = "application/json"
}

$response = Invoke-RestMethod -Method Get -Uri $endpoint -Headers $headers

if ($null -ne $response.data) {
    $response.data | ForEach-Object {
        if ($null -ne $_.id) {
            Write-Output $_.id
        } else {
            Write-Output ($_ | ConvertTo-Json -Compress)
        }
    }
} else {
    $response | ConvertTo-Json -Depth 10
}
