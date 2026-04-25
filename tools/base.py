# tools/base.py
from dataclasses import dataclass
from typing import Any

@dataclass
class ToolResult:
    tool_name: str
    status: str    # SAFE | CONTRAINDICATED | USE_WITH_CAUTION | DATA
    data: Any
    reasoning: str

    def to_string(self):
        return f'[{self.tool_name}] {self.status}: {self.reasoning[:150]}'