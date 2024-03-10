#!/bin/bash
# Execute the first entrypoint script
/scripts/entrypoint.sh

# Execute the second entrypoint script
/scripts/worker-entrypoint.sh
