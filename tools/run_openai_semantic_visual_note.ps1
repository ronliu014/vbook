param(
    [string]$RepoRoot = "E:\projects\my_app\vbook",
    [string]$ExperimentRoot = "F:\vbook\experiments\E20260710-semantic-visual-note",
    [string]$Provider = "openai",
    [string]$LessonId = "lesson-003",
    [string]$Python = "D:\anaconda3\envs\App\python.exe",
    [string]$BaseUrl = "",
    [string]$Model = "gpt-5.5",
    [string]$ReasoningEffort = "xhigh",
    [string]$ApiKeyEnv = "ANTHROPIC_AUTH_TOKEN",
    [double]$TimeoutSeconds = 300
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

$datasetPath = Join-Path $ExperimentRoot "inputs\dataset.json"
if (-not (Test-Path -LiteralPath $datasetPath)) {
    throw "dataset not found: $datasetPath"
}

$dataset = Get-Content -Raw -LiteralPath $datasetPath | ConvertFrom-Json
$lesson = $dataset.lessons | Where-Object { $_.lesson_id -eq $LessonId } | Select-Object -First 1
if ($null -eq $lesson) {
    throw "lesson id not found in dataset: $LessonId"
}

$requestPath = Join-Path $ExperimentRoot ("requests\semantic_visual_note\" + $lesson.title + ".request.json")
$responseDir = Join-Path $ExperimentRoot ("responses\" + $Provider)
$responsePath = Join-Path $responseDir ($lesson.title + ".response.json")

if (-not (Test-Path -LiteralPath $requestPath)) {
    throw "request not found: $requestPath"
}

New-Item -ItemType Directory -Force -Path $responseDir | Out-Null

& $Python `
    (Join-Path $RepoRoot "tools\openai_responses_semantic_visual_adapter.py") `
    --input $requestPath `
    --output $responsePath `
    --base-url $BaseUrl `
    --model $Model `
    --reasoning-effort $ReasoningEffort `
    --api-key-env $ApiKeyEnv `
    --timeout-seconds $TimeoutSeconds `
    --disable-response-storage

if ($LASTEXITCODE -ne 0) {
    throw "model adapter failed with exit code $LASTEXITCODE"
}

Write-Output "response_path=$responsePath"
Write-Output "next_step=ask Codex to render and review this response"
