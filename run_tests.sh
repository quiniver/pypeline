#!/bin/bash

# Run all tests with pytest
echo "Running pytest on all test files..."
python -m pytest tests -v --tb=short --color=yes

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "❌ Some tests failed. Exit code: $exit_code"
fi

exit $exit_code
