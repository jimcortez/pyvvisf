# Windows PowerShell script for building VVISF-GL libraries
# This script builds the VVISF and VVGL libraries for Windows

param(
    [string]$Configuration = "Release",
    [string]$Platform = "x64"
)

Write-Host "Building VVISF-GL libraries for Windows..."
Write-Host "Configuration: $Configuration"
Write-Host "Platform: $Platform"

# Set error action preference to stop on errors
$ErrorActionPreference = "Stop"

try {
    # Get the script directory
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $ProjectRoot = Split-Path -Parent $ScriptDir
    $VVISFDir = Join-Path $ProjectRoot "external\VVISF-GL"
    $WindowsDir = Join-Path $VVISFDir "examples\Windows"
    
    Write-Host "Script directory: $ScriptDir"
    Write-Host "Project root: $ProjectRoot"
    Write-Host "VVISF directory: $VVISFDir"
    Write-Host "Windows examples directory: $WindowsDir"
    
    # Check if VVISF-GL submodule exists
    if (-not (Test-Path (Join-Path $VVISFDir "README.md"))) {
        throw "VVISF-GL submodule not found at $VVISFDir. Please run: git submodule update --init --recursive"
    }
    
    # Check if Windows solution exists
    $SolutionFile = Join-Path $WindowsDir "Windows.sln"
    if (-not (Test-Path $SolutionFile)) {
        throw "Windows solution not found at $SolutionFile"
    }
    
    Write-Host "Found Windows solution: $SolutionFile"
    
    # Find MSBuild
    $MSBuildPath = $null
    
    # Try to find MSBuild in common locations
    $PossiblePaths = @(
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Professional\MSBuild\Current\Bin\MSBuild.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2017\Enterprise\MSBuild\15.0\Bin\MSBuild.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\MSBuild.exe"
    )
    
    foreach ($Path in $PossiblePaths) {
        if (Test-Path $Path) {
            $MSBuildPath = $Path
            Write-Host "Found MSBuild at: $MSBuildPath"
            break
        }
    }
    
    if (-not $MSBuildPath) {
        # Try to find MSBuild in PATH
        try {
            $MSBuildPath = (Get-Command msbuild -ErrorAction Stop).Source
            Write-Host "Found MSBuild in PATH: $MSBuildPath"
        } catch {
            throw "MSBuild not found. Please install Visual Studio Build Tools or Visual Studio."
        }
    }
    
    # Set up build directories
    $VVGLBinDir = Join-Path $VVISFDir "VVGL\bin"
    $VVISFBinDir = Join-Path $VVISFDir "VVISF\bin"
    
    # Create bin directories if they don't exist
    if (-not (Test-Path $VVGLBinDir)) {
        New-Item -ItemType Directory -Path $VVGLBinDir -Force | Out-Null
    }
    if (-not (Test-Path $VVISFBinDir)) {
        New-Item -ItemType Directory -Path $VVISFBinDir -Force | Out-Null
    }
    
    # Build VVGL
    Write-Host "Building VVGL..."
    $VVGLProject = Join-Path $WindowsDir "VVGL\VVGL.vcxproj"
    if (Test-Path $VVGLProject) {
        $VVGLArgs = @(
            $VVGLProject,
            "/p:Configuration=$Configuration",
            "/p:Platform=$Platform",
            "/p:OutDir=$VVGLBinDir\",
            "/verbosity:minimal"
        )
        
        Write-Host "Running: $MSBuildPath $VVGLArgs"
        & $MSBuildPath @VVGLArgs
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to build VVGL"
        }
        Write-Host "✓ VVGL built successfully"
    } else {
        throw "VVGL project not found at $VVGLProject"
    }
    
    # Build VVISF
    Write-Host "Building VVISF..."
    $VVISFProject = Join-Path $WindowsDir "VVISF\VVISF.vcxproj"
    if (Test-Path $VVISFProject) {
        $VVISFArgs = @(
            $VVISFProject,
            "/p:Configuration=$Configuration",
            "/p:Platform=$Platform",
            "/p:OutDir=$VVISFBinDir\",
            "/verbosity:minimal"
        )
        
        Write-Host "Running: $MSBuildPath $VVISFArgs"
        & $MSBuildPath @VVISFArgs
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to build VVISF"
        }
        Write-Host "✓ VVISF built successfully"
    } else {
        throw "VVISF project not found at $VVISFProject"
    }
    
    # Check if libraries were created
    $VVGLLib = Join-Path $VVGLBinDir "VVGL.lib"
    $VVISFLib = Join-Path $VVISFBinDir "VVISF.lib"
    
    if (Test-Path $VVGLLib) {
        Write-Host "✓ VVGL library created: $VVGLLib"
    } else {
        throw "VVGL library not found at expected location: $VVGLLib"
    }
    
    if (Test-Path $VVISFLib) {
        Write-Host "✓ VVISF library created: $VVISFLib"
    } else {
        throw "VVISF library not found at expected location: $VVISFLib"
    }
    
    Write-Host "VVISF-GL libraries built successfully for Windows!"
    Write-Host "Libraries location:"
    Write-Host "  VVGL: $VVGLLib"
    Write-Host "  VVISF: $VVISFLib"
    
} catch {
    Write-Host "Error building VVISF-GL libraries: $_"
    exit 1
} 