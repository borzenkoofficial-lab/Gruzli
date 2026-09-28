from dataclasses import dataclass

@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    task: str
    expected_tools: tuple[str,...]=()
    required_terms: tuple[str,...]=()

CASES=[
 BenchmarkCase('file-edit','Create hello.txt containing Hello Nexum',('write_file',),('Hello Nexum',)),
 BenchmarkCase('python-check','Run Python that calculates 2 + 2',('run_python',),('4',)),
 BenchmarkCase('inspect-project','List workspace files',('list_files',),()),
]