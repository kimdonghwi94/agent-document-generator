"""Debug format parsing."""

import json
from agent_document_generator.models import DocumentFormat, UserQuery

# Test the parsing logic
test_content = json.dumps({
    "question": "Create a simple guide",
    "format": "markdown"
})

print(f"Test content: {test_content}")

try:
    data = json.loads(test_content)
    print(f"Parsed data: {data}")
    
    format_str = data.get("format", "html")
    print(f"Format string: {format_str}")
    
    # Test DocumentFormat enum
    print(f"Available formats: {list(DocumentFormat)}")
    
    format_obj = DocumentFormat(format_str)
    print(f"Format object: {format_obj}")
    print(f"Format value: {format_obj.value}")
    
    query = UserQuery(
        question=data.get("question", test_content),
        format=format_obj,
        context=data.get("context"),
        metadata=data.get("metadata")
    )
    
    print(f"Created UserQuery:")
    print(f"  Question: {query.question}")
    print(f"  Format: {query.format}")
    print(f"  Format value: {query.format.value}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()