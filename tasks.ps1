param(
  [ValidateSet('init','run','test')]
  [string]$task = 'run'
)

switch ($task) {
  'init' {
    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -U pip
    pip install -e .[dev]
  }
  'run' {
    .\.venv\Scripts\Activate.ps1
    uvicorn src.server:app --reload --port 8000
  }
  'test' {
    .\.venv\Scripts\Activate.ps1
    pytest -q
  }
}
