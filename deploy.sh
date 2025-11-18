#!/bin/bash

# Load environment variables from .env (if present)
if [[ -f ".env" ]]; then
    set -o allexport
    # shellcheck source=/dev/null
    source ".env"
    set +o allexport
else
    echo "Warning: .env file not found — using defaults if present in script."
fi

# Read ignore list
IGNORE_LIST=()
if [[ -f ".gitignore" ]]; then
    while IFS= read -r line; do
        [[ -n "$line" ]] && IGNORE_LIST+=("--exclude=$line")
    done < .gitignore
else
    echo "Warning: .gitignore not found."
fi

# Create tarball excluding ignored files
tar czf temp.tar.gz "${IGNORE_LIST[@]}" .

# Clean remote directory
ssh "$REMOTE_USER@$REMOTE_HOST" "rm -r $REMOTE_PATH && mkdir -p $REMOTE_PATH"

# Copy tarball to remote
scp temp.tar.gz "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/temp.tar.gz"

# Optional: SSH into remote and extract
ssh "$REMOTE_USER@$REMOTE_HOST" "tar xzf $REMOTE_PATH/temp.tar.gz -C $REMOTE_PATH && rm $REMOTE_PATH/temp.tar.gz && systemctl restart $REMOTE_SERVICE"

# Clean up local tarball
rm temp.tar.gz