import sys
sys.path.insert(0, '.')
from src import ingest
result = ingest.load_csv('input_examples/sample-input.csv')
if result.get('success'):
    print(f'Loaded {result.get("count", 0)} records')
else:
    print(f'Error: {result.get("error")}')
