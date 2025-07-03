#!/bin/bash
set -e

echo "Cleaning up duplicated Linux configurations in Makefiles..."

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VVISF_DIR="$PROJECT_ROOT/external/VVISF-GL"

cd "$VVISF_DIR"

# Function to clean up duplicated Linux configurations
cleanup_linux_config() {
    local makefile="$1"
    echo "Cleaning up $makefile..."
    
    # Create a backup
    cp "$makefile" "${makefile}.backup"
    
    # Use awk to remove duplicates
    awk '
    BEGIN { in_linux_section = 0; linux_config_count = 0; }
    /^else ifeq \(\$\(shell uname\),Linux\)/ {
        if (linux_config_count == 0) {
            # First occurrence - keep it and start collecting
            in_linux_section = 1
            linux_config_count = 1
            print
            next
        } else {
            # Subsequent occurrences - skip the entire section
            in_linux_section = 1
            linux_config_count++
            next
        }
    }
    /^else ifeq/ {
        if (in_linux_section) {
            # End of Linux section, start of next section
            in_linux_section = 0
        }
        print
        next
    }
    {
        if (in_linux_section && linux_config_count == 1) {
            # Keep lines from first Linux section
            print
        } else if (!in_linux_section) {
            # Keep lines outside Linux sections
            print
        }
        # Skip lines from duplicate Linux sections
    }
    ' "$makefile" > "${makefile}.tmp"
    
    # Replace original with cleaned version
    mv "${makefile}.tmp" "$makefile"
    
    echo "✓ Cleaned up $makefile"
}

# Clean up both Makefiles
cleanup_linux_config "VVGL/Makefile"
cleanup_linux_config "VVISF/Makefile"

echo "✓ Cleanup completed successfully!"
echo "Backup files created:"
echo "  - VVGL/Makefile.backup"
echo "  - VVISF/Makefile.backup" 