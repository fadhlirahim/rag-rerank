#!/bin/bash
set -e

echo "Setting up RAG Rerank PoC with uv and mise..."

# Function to install uv and ensure it's available
install_uv() {
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add potential uv binary locations to PATH, prioritizing ~/.local/bin
    export PATH="$HOME/.local/bin:$HOME/bin:$HOME/.cargo/bin:$PATH"

    # Wait a moment for installation to complete
    sleep 1

    # Try to find uv
    if command -v uv &> /dev/null; then
        echo "uv installed successfully!"
        return 0
    fi

    # If not found, try to locate it directly, checking ~/.local/bin first
    for possible_path in "$HOME/.local/bin/uv" "$HOME/bin/uv" "$HOME/.cargo/bin/uv"; do
        if [ -x "$possible_path" ]; then
            echo "Found uv at $possible_path"
            export PATH="$(dirname "$possible_path"):$PATH"
            return 0
        fi
    done

    echo "ERROR: uv installation completed but command not found."
    echo "The installer reports success but the binary couldn't be located."
    echo "Common installation locations checked:"
    echo " - $HOME/.local/bin/uv (expected location)"
    echo " - $HOME/bin/uv"
    echo " - $HOME/.cargo/bin/uv"
    echo "You may need to install uv manually or restart your terminal."
    return 1
}

# Function to install mise and ensure it's available
install_mise() {
    echo "Installing mise..."
    curl https://mise.run | sh

    # Add potential mise binary locations to PATH
    export PATH="$HOME/.local/bin:$HOME/bin:$HOME/.mise/bin:$PATH"

    # Wait a moment for installation to complete
    sleep 1

    # Try to find mise
    if command -v mise &> /dev/null; then
        echo "mise installed successfully!"
        return 0
    fi

    # If not found, try to locate it directly
    for possible_path in "$HOME/.local/bin/mise" "$HOME/bin/mise" "$HOME/.mise/bin/mise"; do
        if [ -x "$possible_path" ]; then
            echo "Found mise at $possible_path"
            export PATH="$(dirname "$possible_path"):$PATH"
            return 0
        fi
    done

    echo "ERROR: mise installation completed but command not found."
    echo "The installer reports success but the binary couldn't be located."
    echo "Common installation locations checked:"
    echo " - $HOME/.local/bin/mise"
    echo " - $HOME/bin/mise"
    echo " - $HOME/.mise/bin/mise"
    echo "You may need to install mise manually or restart your terminal."
    return 1
}

# Handle uv installation/location
if command -v uv &> /dev/null; then
    echo "uv is already installed."
    UV_BIN="uv"
else
    install_uv
    if command -v uv &> /dev/null; then
        UV_BIN="uv"
    else
        # Try to find uv binary directly as a fallback, prioritizing ~/.local/bin
        for possible_path in "$HOME/.local/bin/uv" "$HOME/bin/uv" "$HOME/.cargo/bin/uv"; do
            if [ -x "$possible_path" ]; then
                echo "Using direct path to uv: $possible_path"
                UV_BIN="$possible_path"
                break
            fi
        done

        # If still not found, offer manual installation instructions
        if [ -z "$UV_BIN" ]; then
            echo "Failed to use uv. You can try installing it manually with:"
            echo "  curl -sSf https://astral.sh/uv/install.sh | bash"
            echo "  Then add ~/.local/bin to your PATH and restart your terminal."
            exit 1
        fi
    fi
    echo "Using uv at: $(which uv 2>/dev/null || echo "$UV_BIN")"
fi

# Handle mise installation/location
if command -v mise &> /dev/null; then
    echo "mise is already installed."
    MISE_BIN="mise"
else
    install_mise
    if command -v mise &> /dev/null; then
        MISE_BIN="mise"
    else
        # Try to find mise binary directly as a fallback
        for possible_path in "$HOME/.local/bin/mise" "$HOME/bin/mise" "$HOME/.mise/bin/mise"; do
            if [ -x "$possible_path" ]; then
                echo "Using direct path to mise: $possible_path"
                MISE_BIN="$possible_path"
                break
            fi
        done

        # If still not found, offer manual installation instructions
        if [ -z "$MISE_BIN" ]; then
            echo "Failed to use mise. You can try installing it manually with:"
            echo "  curl -sSf https://mise.jdx.dev/install.sh | bash"
            echo "  Then restart your terminal and run this script again."
            exit 1
        fi
    fi
    echo "Using mise at: $(which mise 2>/dev/null || echo "$MISE_BIN")"
fi

# Ensure Python version is installed
echo "Installing Python via mise..."
$MISE_BIN install python@3.11.12

# Create virtual environment using uv
echo "Creating virtual environment with uv..."
$UV_BIN venv

# Install all dependencies (backend + frontend)
echo "Installing all dependencies..."
$MISE_BIN run install-all

# Copy env.example to .env if it doesn't exist
if [ ! -f .env ] && [ -f env.example ]; then
    echo "Creating .env file from template..."
    cp env.example .env
    echo "Please edit the .env file to add your API keys."
fi

echo ""
echo "Setup complete! To use the new tools, you may need to open a new terminal or run:"
echo "  export PATH=\"$HOME/.cargo/bin:$HOME/.local/bin:\$PATH\""
echo ""
echo "After that, you can run the application using:"
echo ""
echo "Backend tasks:"
echo "  mise run start      # Start the backend server"
echo "  mise run dev        # Run the backend development server"
echo "  mise run test       # Run tests with verbose output"
echo "  mise run lint       # Run linting checks"
echo "  mise run format     # Format code and fix auto-fixable issues"
echo "  mise run check      # Run type checking with explicit bases"
echo ""
echo "Frontend tasks:"
echo "  mise run frontend-install  # Install frontend dependencies"
echo "  mise run frontend-dev     # Start the frontend development server"
echo "  mise run frontend-build   # Build the frontend for production"
echo "  mise run frontend-preview # Preview the production build"
echo ""
echo "Composite tasks:"
echo "  mise run install-all     # Install all dependencies (backend + frontend)"
echo "  mise run dev-all        # Start both backend and frontend development servers"
echo ""
echo "Don't forget to edit your .env file with your API keys!"