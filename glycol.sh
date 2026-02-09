#!/usr/bin/env bash
# Glycol launcher - runs the application in the background

set -euo pipefail
usage() {
    exec python -m glycol --help
}
for arg in "$@"; do
    case "$arg" in
        -h|--help)
            usage
            ;;
    esac
done

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment if it exists
if [ -d "$SCRIPT_DIR/.venv" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Launch glycol in the background
# Python handles its own logging to files
cd "$SCRIPT_DIR"
python -m glycol "$@" &

# Get the PID of the backgrounded process
PID=$!

# Detach from the shell so it survives terminal closure
disown

echo "Glycol launched in background (PID: $PID)"
echo "Check logs/ directory for output"
