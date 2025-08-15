#!/bin/bash
# setup-apt-repo.sh - Set up APT repository for rxiv-maker
set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() { echo -e "${BLUE}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPO_DIR="$PROJECT_ROOT/apt-repo"
GPG_KEY_ID=""
DEB_FILE=""
BRANCH_NAME="apt-repo"

show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Set up and manage APT repository for rxiv-maker

OPTIONS:
    -k, --key KEY      GPG key ID for signing repository
    -d, --deb FILE     Debian package file to add to repository
    -i, --init         Initialize new repository
    -u, --update       Update existing repository
    -p, --publish      Publish repository to GitHub Pages
    -h, --help         Show this help message

EXAMPLES:
    $0 --init --key ABCD1234                    # Initialize new repo
    $0 --deb dist/rxiv-maker_1.5.10-1_all.deb   # Add package to repo
    $0 --update --publish                       # Update and publish

ENVIRONMENT VARIABLES:
    RXIV_APT_GPG_KEY     Default GPG key for repository signing
    RXIV_APT_BRANCH      Git branch for repository (default: apt-repo)

EOF
}

# Parse arguments
INIT=false
UPDATE=false
PUBLISH=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -k|--key)
            GPG_KEY_ID="$2"
            shift 2
            ;;
        -d|--deb)
            DEB_FILE="$2"
            shift 2
            ;;
        -i|--init)
            INIT=true
            shift
            ;;
        -u|--update)
            UPDATE=true
            shift
            ;;
        -p|--publish)
            PUBLISH=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Use environment variables as fallbacks
GPG_KEY_ID="${GPG_KEY_ID:-${RXIV_APT_GPG_KEY:-}}"
BRANCH_NAME="${BRANCH_NAME:-${RXIV_APT_BRANCH:-apt-repo}}"

# Validate environment
validate_environment() {
    log "Validating APT repository environment..."

    # Check for required tools
    local required_tools=("reprepro" "git" "gpg")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            error "Required tool not found: $tool"
            case $tool in
                reprepro)
                    warn "Install with: sudo apt-get install reprepro"
                    ;;
                git)
                    warn "Install git from your package manager"
                    ;;
                gpg)
                    warn "Install with: sudo apt-get install gnupg"
                    ;;
            esac
            exit 1
        fi
    done

    # Validate GPG key
    if [[ -n "$GPG_KEY_ID" ]]; then
        if ! gpg --list-secret-keys "$GPG_KEY_ID" >/dev/null 2>&1; then
            error "GPG key not found or not accessible: $GPG_KEY_ID"
            warn "List available keys with: gpg --list-secret-keys"
            exit 1
        fi
        log "Using GPG key: $GPG_KEY_ID"
    elif [[ "$INIT" == "true" ]] || [[ -n "$DEB_FILE" ]]; then
        error "GPG key required for repository operations"
        warn "Use --key <KEY_ID> or set RXIV_APT_GPG_KEY environment variable"
        exit 1
    fi

    success "Environment validation passed"
}

# Initialize repository
initialize_repo() {
    log "Initializing APT repository..."

    if [[ -d "$REPO_DIR" ]]; then
        warn "Repository directory already exists: $REPO_DIR"
        read -p "Do you want to reinitialize? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Skipping initialization"
            return 0
        fi
        rm -rf "$REPO_DIR"
    fi

    # Create repository structure
    mkdir -p "$REPO_DIR"/{conf,dists,pool,incoming}

    # Create distributions file
    cat > "$REPO_DIR/conf/distributions" << EOF
Origin: Rxiv-Maker Project
Label: Rxiv-Maker APT Repository
Suite: stable
Codename: stable
Architectures: amd64 arm64 all
Components: main
Description: APT repository for rxiv-maker - Automated LaTeX article generation
SignWith: $GPG_KEY_ID
DebIndices: Packages Release . .gz .bz2
DscIndices: Sources Release .gz .bz2
Contents: .gz .bz2
EOF

    # Create options file
    cat > "$REPO_DIR/conf/options" << EOF
# reprepro configuration options for rxiv-maker APT repository
verbose
ask-passphrase
export=changed
verify
EOF

    # Initialize git repository
    cd "$REPO_DIR"
    git init
    git config user.name "Rxiv-Maker Repository Manager"
    git config user.email "rxiv.maker@gmail.com"

    # Create README
    cat > README.md << 'EOF'
# Rxiv-Maker APT Repository

This repository contains Debian packages for rxiv-maker.

## Usage

Add this repository to your system:

```bash
# Add GPG key
curl -fsSL https://raw.githubusercontent.com/henriqueslab/rxiv-maker/apt-repo/pubkey.gpg | sudo gpg --dearmor -o /usr/share/keyrings/rxiv-maker.gpg

# Add repository
echo "deb [arch=amd64] https://raw.githubusercontent.com/henriqueslab/rxiv-maker/apt-repo stable main" | sudo tee /etc/apt/sources.list.d/rxiv-maker.list

# Update package list
sudo apt update

# Install rxiv-maker
sudo apt install rxiv-maker
```

## Repository Structure

- `dists/` - Distribution metadata
- `pool/` - Package files
- `conf/` - Repository configuration
- `pubkey.gpg` - GPG public key for package verification

## Packages

- `rxiv-maker` - Main package with all dependencies
EOF

    # Export GPG public key
    log "Exporting GPG public key..."
    gpg --armor --export "$GPG_KEY_ID" > pubkey.gpg

    # Add files to git
    git add .
    git commit -m "Initialize APT repository for rxiv-maker

- Add repository configuration
- Export GPG public key
- Create initial README"

    success "APT repository initialized successfully"
}

# Add package to repository
add_package() {
    local deb_file="$1"

    if [[ ! -f "$deb_file" ]]; then
        error "Package file not found: $deb_file"
        exit 1
    fi

    log "Adding package to repository: $(basename "$deb_file")"

    cd "$REPO_DIR"

    # Copy package to incoming directory
    cp "$deb_file" incoming/

    # Add package to repository
    local package_name=$(basename "$deb_file")
    if reprepro --ask-passphrase -Vb . includedeb stable "incoming/$package_name"; then
        success "Package added successfully"
        rm "incoming/$package_name"
    else
        error "Failed to add package to repository"
        exit 1
    fi

    # Commit changes
    git add .
    git commit -m "Add package: $package_name

- Updated repository metadata
- Package available in stable/main component"

    success "Repository updated with new package"
}

# Update repository
update_repository() {
    log "Updating repository metadata..."

    cd "$REPO_DIR"

    # Export repository (regenerate metadata)
    if reprepro --ask-passphrase -Vb . export; then
        success "Repository metadata updated"
    else
        error "Failed to update repository metadata"
        exit 1
    fi

    # Update package list in README
    update_readme

    # Commit changes
    git add .
    git commit -m "Update repository metadata

- Regenerated package indices
- Updated README with current packages" || true

    success "Repository update completed"
}

# Update README with package list
update_readme() {
    log "Updating README with package information..."

    cd "$REPO_DIR"

    # Get package list
    local packages=""
    if [[ -f "dists/stable/main/binary-all/Packages" ]]; then
        packages=$(grep -E "^Package:|^Version:|^Description:" dists/stable/main/binary-all/Packages | \
                  paste - - - | \
                  sed 's/Package: //; s/Version: / (/; s/Description: /) - /; s/$//')
    fi

    # Update README
    local readme_temp=$(mktemp)
    awk '
        /^## Packages/ {
            print $0
            print ""
            print "- `rxiv-maker` - Main package with all dependencies"
            if (packages != "") {
                print packages
            }
            skip = 1
            next
        }
        skip && /^##/ { skip = 0 }
        !skip { print }
    ' packages="$packages" README.md > "$readme_temp"

    mv "$readme_temp" README.md
}

# Publish repository
publish_repository() {
    log "Publishing repository to GitHub..."

    cd "$REPO_DIR"

    # Check if we have commits to push
    if git diff --cached --quiet && git diff-index --quiet HEAD --; then
        log "No changes to publish"
        return 0
    fi

    # Push to apt-repo branch
    if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
        log "Switching to branch: $BRANCH_NAME"
        git checkout "$BRANCH_NAME"
    else
        log "Creating new branch: $BRANCH_NAME"
        git checkout -b "$BRANCH_NAME"
    fi

    # Push to origin
    log "Pushing to origin/$BRANCH_NAME..."
    if git push origin "$BRANCH_NAME"; then
        success "Repository published successfully"
        log "Repository available at: https://raw.githubusercontent.com/henriqueslab/rxiv-maker/apt-repo"
    else
        error "Failed to push repository"
        warn "Make sure you have push access to the repository"
        exit 1
    fi
}

# List packages in repository
list_packages() {
    log "Packages in repository:"

    cd "$REPO_DIR"

    if reprepro -b . list stable; then
        success "Package listing completed"
    else
        warn "No packages found in repository"
    fi
}

# Main execution
main() {
    log "Starting APT repository management for rxiv-maker"
    log "Repository directory: $REPO_DIR"
    log "Branch: $BRANCH_NAME"

    validate_environment

    if [[ "$INIT" == "true" ]]; then
        initialize_repo
    fi

    if [[ -n "$DEB_FILE" ]]; then
        add_package "$DEB_FILE"
    fi

    if [[ "$UPDATE" == "true" ]]; then
        update_repository
    fi

    if [[ "$PUBLISH" == "true" ]]; then
        publish_repository
    fi

    # Show final status
    if [[ -d "$REPO_DIR" ]]; then
        list_packages
    fi

    success "APT repository management completed successfully!"

    # Show usage instructions
    if [[ -f "$REPO_DIR/pubkey.gpg" ]]; then
        cat << EOF

📦 Repository Usage Instructions:

1. Add GPG key:
   curl -fsSL https://raw.githubusercontent.com/henriqueslab/rxiv-maker/$BRANCH_NAME/pubkey.gpg | sudo gpg --dearmor -o /usr/share/keyrings/rxiv-maker.gpg

2. Add repository:
   echo "deb [arch=amd64] https://raw.githubusercontent.com/henriqueslab/rxiv-maker/apt-repo stable main" | sudo tee /etc/apt/sources.list.d/rxiv-maker.list

3. Install package:
   sudo apt update && sudo apt install rxiv-maker

EOF
    fi
}

# Run main function
main "$@"
