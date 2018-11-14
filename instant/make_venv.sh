PYTHON_EXEC="$(which python3.7)"
if [ -z "${PYTHON_EXEC}" ]; then
    PYTHON_EXEC="$(which python3.6)"
fi
if [ -z "${PYTHON_EXEC}" ]; then
    echo "Could not find Python 3.7 or 3.6 executable"
    return 1
fi

set -e

"${PYTHON_EXEC}" -m venv ./py3_venv
./py3_venv/bin/pip3 install -r requirements.txt
