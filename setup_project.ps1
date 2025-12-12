# ============================================================================
# Script de Setup Automatique - Resource Server (WINDOWS)
# Auteur: Youness
# Description: Crée toute la structure du projet sur Windows
# ============================================================================

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  SETUP AUTOMATIQUE - RESOURCE SERVER (WINDOWS)" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 1. Vérifications
# ============================================================================

Write-Host "[ÉTAPE] Vérification des prérequis..." -ForegroundColor Blue

# Vérifier Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python n'est pas installé. Installez Python 3.9+ depuis python.org" -ForegroundColor Red
    exit 1
}
Write-Host "[✓] Python trouvé" -ForegroundColor Green

# Vérifier pip
if (!(Get-Command pip -ErrorAction SilentlyContinue)) {
    Write-Host "❌ pip n'est pas installé." -ForegroundColor Red
    exit 1
}
Write-Host "[✓] pip trouvé" -ForegroundColor Green

# ============================================================================
# 2. Création de la structure
# ============================================================================

Write-Host "[ÉTAPE] Création de la structure du projet..." -ForegroundColor Blue

# Créer dossiers
New-Item -ItemType Directory -Force -Path "docs" | Out-Null
New-Item -ItemType Directory -Force -Path "tests" | Out-Null
New-Item -ItemType Directory -Force -Path "scripts" | Out-Null

Write-Host "[✓] Dossiers créés : docs/, tests/, scripts/" -ForegroundColor Green

# ============================================================================
# 3. Créer .gitignore
# ============================================================================

Write-Host "[ÉTAPE] Création de .gitignore..." -ForegroundColor Blue

$gitignore = @"
# Python
__pycache__/
*.py[cod]
*`$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# Environment variables
.env
*.env
!.env.example

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/
*.cover

# Logs
*.log
"@

Set-Content -Path ".gitignore" -Value $gitignore
Write-Host "[✓] .gitignore créé" -ForegroundColor Green

# ============================================================================
# 4. Créer l'environnement virtuel
# ============================================================================

Write-Host "[ÉTAPE] Création de l'environnement virtuel..." -ForegroundColor Blue

if (Test-Path "venv") {
    Write-Host "[!] venv existe déjà, skip..." -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "[✓] Environnement virtuel créé" -ForegroundColor Green
}

# ============================================================================
# 5. Activer et installer dépendances
# ============================================================================

Write-Host "[ÉTAPE] Installation des dépendances..." -ForegroundColor Blue

# Activer venv
& ".\venv\Scripts\Activate.ps1"

# Installer requirements
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    Write-Host "[✓] Dépendances installées" -ForegroundColor Green
} else {
    Write-Host "[!] requirements.txt non trouvé, skip installation" -ForegroundColor Yellow
}

# ============================================================================
# 6. Créer .env depuis .env.example
# ============================================================================

Write-Host "[ÉTAPE] Configuration de l'environnement..." -ForegroundColor Blue

if (!(Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "[✓] .env créé depuis .env.example" -ForegroundColor Green
        Write-Host "[!] ⚠️  IMPORTANT: Éditer .env avec les valeurs d'Omar (IdP)" -ForegroundColor Yellow
    } else {
        Write-Host "[!] .env.example non trouvé, skip..." -ForegroundColor Yellow
    }
} else {
    Write-Host "[!] .env existe déjà, skip..." -ForegroundColor Yellow
}

# ============================================================================
# 7. Vérifications finales
# ============================================================================

Write-Host "[ÉTAPE] Vérifications finales..." -ForegroundColor Blue
Write-Host ""
Write-Host "Structure du projet:" -ForegroundColor Cyan
Get-ChildItem -Recurse -Depth 1 | Select-Object FullName

# ============================================================================
# 8. Résumé
# ============================================================================

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Green
Write-Host "✓ SETUP TERMINÉ AVEC SUCCÈS !" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Prochaines étapes:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Activer l'environnement virtuel:" -ForegroundColor White
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Éditer .env avec les valeurs d'Omar:" -ForegroundColor White
Write-Host "   notepad .env" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Lancer l'application:" -ForegroundColor White
Write-Host "   Option A - Un seul composant:" -ForegroundColor Gray
Write-Host "     python app.py" -ForegroundColor Yellow
Write-Host "   Option B - Tous les composants (recommandé):" -ForegroundColor Gray
Write-Host "     python start_all.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Tester l'API:" -ForegroundColor White
Write-Host "   curl http://localhost:5000/api/health" -ForegroundColor Yellow
Write-Host "   # ou dans le navigateur" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Lancer les tests:" -ForegroundColor White
Write-Host "   pytest tests/ -v" -ForegroundColor Yellow
Write-Host ""
Write-Host "Documentation disponible dans:" -ForegroundColor Cyan
Write-Host "  - README.md           : Guide complet"
Write-Host "  - QUICKSTART.md       : Démarrage rapide"
Write-Host "  - TODO.md             : Ta checklist"
Write-Host "  - docs\API.md         : Documentation API"
Write-Host "  - docs\SECURITY.md    : Documentation sécurité"
Write-Host ""
Write-Host "========================================================================" -ForegroundColor Green