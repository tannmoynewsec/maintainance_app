#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploys the Maintenance Support Scheduler app to Azure App Service
.DESCRIPTION
    This script deploys the application to an Azure App Service instance.
    It handles authentication, resource creation if needed, and code deployment.
.NOTES
    Requires the Azure CLI to be installed and logged in.
#>

# Configuration Variables - modify these as needed
$ResourceGroupName = "clientreporting-dev-rg"
$Location = "westeurope"  # Change to your preferred Azure region
$AppServicePlanName = "maintainance-app-plan"
$WebAppName = "maintainance-scheduler"  # This will be your app's URL: https://$WebAppName.azurewebsites.net
$PythonVersion = "3.10"  # Must match runtime.txt
$AppServiceSku = "F1"    # Explicitly using F1 (Free) tier for Azure App Service

# Color output functions
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success($message) {
    Write-ColorOutput Green "[SUCCESS] $message"
}

function Write-Info($message) {
    Write-ColorOutput Cyan "[INFO] $message"
}

function Write-Warning($message) {
    Write-ColorOutput Yellow "[WARNING] $message"
}

function Write-Error($message) {
    Write-ColorOutput Red "[ERROR] $message"
}

# Check if Azure CLI is installed
Write-Info "Checking if Azure CLI is installed..."
try {
    az --version > $null
    Write-Success "Azure CLI is installed."
} 
catch {
    Write-Error "Azure CLI is not installed. Please install it from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
}

# Check if logged in to Azure
Write-Info "Checking if you're logged in to Azure..."
$loginStatus = az account show 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Info "Not logged in. Please log in to Azure..."
    az login
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to log in to Azure. Please try again."
        exit 1
    }
    Write-Success "Successfully logged in to Azure."
} else {
    $accountInfo = $loginStatus | ConvertFrom-Json
    Write-Success "Already logged in as $($accountInfo.user.name)"
}

# Create Resource Group if it doesn't exist
Write-Info "Checking if Resource Group '$ResourceGroupName' exists..."
$rgExists = az group exists --name $ResourceGroupName
if ($rgExists -eq "true") {
    Write-Info "Resource Group '$ResourceGroupName' already exists."
} else {
    Write-Info "Creating Resource Group '$ResourceGroupName'..."
    az group create --name $ResourceGroupName --location $Location
    Write-Success "Resource Group created successfully."
}

# Create App Service Plan if it doesn't exist
Write-Info "Checking if App Service Plan '$AppServicePlanName' exists..."
$appPlanExists = az appservice plan list --resource-group $ResourceGroupName --query "[?name=='$AppServicePlanName'].name" -o tsv
if ($appPlanExists -eq $AppServicePlanName) {
    Write-Info "App Service Plan '$AppServicePlanName' already exists."
} else {
    Write-Info "Creating App Service Plan '$AppServicePlanName'..."
    az appservice plan create --name $AppServicePlanName --resource-group $ResourceGroupName --sku $AppServiceSku --is-linux
    Write-Success "App Service Plan created successfully."
}

# Create Web App if it doesn't exist
Write-Info "Checking if Web App '$WebAppName' exists..."
$webAppExists = az webapp list --resource-group $ResourceGroupName --query "[?name=='$WebAppName'].name" -o tsv
if ($webAppExists -eq $WebAppName) {
    Write-Info "Web App '$WebAppName' already exists."
} else {    Write-Info "Creating Web App '$WebAppName' on Free tier plan..."
    az webapp create --name $WebAppName --resource-group $ResourceGroupName --plan $AppServicePlanName --runtime "python:3.10"
    Write-Success "Web App created successfully on free tier App Service Plan."
}

# Set deployment specific app settings
Write-Info "Configuring application settings..."
az webapp config set --name $WebAppName --resource-group $ResourceGroupName --startup-file "startup.txt" 

# Update application settings
Write-Info "Setting environment variables..."
az webapp config appsettings set --name $WebAppName --resource-group $ResourceGroupName --settings `
    WEBSITE_HTTPLOGGING_RETENTION_DAYS=3 `
    SCM_DO_BUILD_DURING_DEPLOYMENT=true `
    ENABLE_ORYX_BUILD=true `
    PYTHONPATH="/home/site/wwwroot" `
    SCM_PYTHON_VERSION="3.10" `
    PYTHON_VERSION="3.10" `
    WEBSITE_PYTHON_VERSION="3.10" `
    PYTHON_EXT_PATH="" `
    SCM_USE_DEPLOYMENT_CREDENTIALS=true `
    BUILD_FLAGS="" `
    SCM_COMMAND_IDLE_TIMEOUT=3600 `
    ASPNETCORE_ENVIRONMENT="Production" `
    ADMIN_USERNAME="admin" `
    ADMIN_PASSWORD="admin123" `
    APP_SERVICE_PLAN_TIER="Free"

# Configure logging
Write-Info "Enabling application logging..."
az webapp log config --name $WebAppName --resource-group $ResourceGroupName --application-logging filesystem --detailed-error-messages true --failed-request-tracing true --web-server-logging filesystem

# Deploy the application using ZIP deployment (more reliable than Git deployment)
Write-Info "Deploying application code using ZIP deployment..."

# Create a ZIP archive of the application
Write-Info "Creating ZIP archive of the application..."
$zipPath = ".\app.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath
}

# Create a ZIP file excluding unnecessary files
Add-Type -AssemblyName System.IO.Compression.FileSystem
$compressionLevel = [System.IO.Compression.CompressionLevel]::Optimal
$includeBaseDirectory = $false

# Create temporary directory for deployment files
$tempDir = ".\temp_deploy"
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copy only needed files (exclude git, temp files, etc.)
Write-Info "Preparing deployment files..."
Get-ChildItem -Path "." -Exclude "__pycache__", ".git", ".vscode", "app.zip", "temp_deploy" | 
    Where-Object { $_.Name -notlike "*.pyc" } | 
    ForEach-Object { 
        Copy-Item -Path $_.FullName -Destination "$tempDir\$($_.Name)" -Recurse -Force
    }

# For Azure deployment, also copy data files to the root directory
Write-Info "Copying data files to root for Azure deployment..."
if (Test-Path ".\data") {
    Copy-Item -Path ".\data\personnel.json" -Destination "$tempDir\personnel.json" -Force
    # holidays.json no longer needed
    Copy-Item -Path ".\data\settings.json" -Destination "$tempDir\settings.json" -Force
}

# Create ZIP from the temp directory
[System.IO.Compression.ZipFile]::CreateFromDirectory($tempDir, $zipPath, $compressionLevel, $includeBaseDirectory)

# Deploy using ZIP deployment
Write-Info "Deploying using ZIP deployment..."
az webapp deployment source config-zip --resource-group $ResourceGroupName --name $WebAppName --src $zipPath

if ($LASTEXITCODE -eq 0) {
    Write-Success "Application deployed successfully via ZIP deployment!"
    Write-Info "Your application is now available at: https://$WebAppName.azurewebsites.net"
    
    # Cleanup
    if (Test-Path $tempDir) {
        Remove-Item -Path $tempDir -Recurse -Force
    }
    
    if (Test-Path $zipPath) {
        Remove-Item $zipPath
    }
} else {
    Write-Error "ZIP deployment failed. Please check the error messages above."
}

# Verify that we're using Free tier
Write-Info "Verifying App Service Plan tier..."
$planSku = az appservice plan show --name $AppServicePlanName --resource-group $ResourceGroupName --query "sku.name" -o tsv
if ($planSku -eq $AppServiceSku) {
    Write-Success "Confirmed: App Service Plan is using $AppServiceSku (Free) tier."
} else {
    Write-Warning "Warning: App Service Plan is using $planSku tier, not the expected $AppServiceSku (Free) tier."
    Write-Warning "For Free tier deployment, you may need to delete this service and recreate it with the F1 SKU."
}

# Open the web application in the default browser
Write-Info "Opening application in browser..."
Start-Process "https://$WebAppName.azurewebsites.net"
