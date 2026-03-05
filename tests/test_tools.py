"""Tests para las herramientas (AgentTool)."""

import pytest

from agente_ia.infrastructure.llm_client import LLMClient, MockLLMProvider
from agente_ia.models import AgentTask, CodeFile, ContextBundle, TaskType
from agente_ia.tools.code_analyzer import CodeAnalyzer, CodebaseIndex
from agente_ia.tools.code_generation_tool import CodeGenerationTool
from agente_ia.tools.context_builder import ContextBuilder
from agente_ia.tools.doc_generator_tool import DocGeneratorTool
from agente_ia.tools.static_analysis_tool import StaticAnalysisTool


SAMPLE_PYTHON = """\
def suma(a: int, b: int) -> int:
    return a + b

class Calculadora:
    def multiplica(self, x, y):
        return x * y
"""


# ---------------------------------------------------------------------------
# CodeAnalyzer
# ---------------------------------------------------------------------------

def test_build_index_extracts_symbols():
    analyzer = CodeAnalyzer()
    files = [CodeFile(path="calc.py", content=SAMPLE_PYTHON, language="python")]
    index = analyzer.build_index(files)

    names = [s.name for s in index.symbols]
    assert "suma" in names
    assert "Calculadora" in names
    assert "Calculadora.multiplica" in names


def test_codebase_index_find_symbol():
    analyzer = CodeAnalyzer()
    files = [CodeFile(path="calc.py", content=SAMPLE_PYTHON, language="python")]
    index = analyzer.build_index(files)

    results = index.find_symbol("suma")
    assert len(results) >= 1
    assert results[0].kind == "function"


def test_codebase_index_summary():
    index = CodebaseIndex(
        files=[CodeFile(path="a.py", content="pass", language="python")]
    )
    summary = index.summary()
    assert "1 archivos" in summary


def test_code_analyzer_execute_task():
    analyzer = CodeAnalyzer()
    files = [CodeFile(path="calc.py", content=SAMPLE_PYTHON, language="python")]
    analyzer.build_index(files)

    task = AgentTask(
        tipo=TaskType.EXPLORE_CODEBASE,
        descripcion="Buscar suma",
        input_context={"query": "suma"},
    )
    result = analyzer.execute(task, ContextBundle())
    assert result.success
    assert "suma" in result.output


# ---------------------------------------------------------------------------
# ContextBuilder
# ---------------------------------------------------------------------------

def test_context_builder_selects_relevant_files():
    files = [
        CodeFile(path="auth.py", content="def login(): pass", language="python"),
        CodeFile(path="main.py", content="def main(): pass", language="python"),
    ]
    analyzer = CodeAnalyzer()
    index = analyzer.build_index(files)
    builder = ContextBuilder(index=index)

    task = AgentTask(
        tipo=TaskType.GENERATE_CODE,
        descripcion="Añadir autenticación",
        input_context={"file_path": "auth.py"},
    )
    bundle = builder.build_context(task)
    paths = [f.path for f in bundle.files]
    assert "auth.py" in paths


def test_format_context_for_prompt():
    files = [CodeFile(path="x.py", content="x = 1", language="python")]
    index = CodebaseIndex(files=files)
    builder = ContextBuilder(index=index, project_rules=["Usa snake_case"])

    bundle = ContextBundle(files=files, project_rules=["Usa snake_case"])
    formatted = builder.format_context_for_prompt(bundle)
    assert "x.py" in formatted
    assert "snake_case" in formatted


# ---------------------------------------------------------------------------
# CodeGenerationTool
# ---------------------------------------------------------------------------

def test_code_generation_tool_generates_patch():
    llm = LLMClient(provider=MockLLMProvider("def nueva_funcion(): return 42"))
    files = [CodeFile(path="app.py", content="pass", language="python")]
    index = CodebaseIndex(files=files)
    builder = ContextBuilder(index=index)
    tool = CodeGenerationTool(llm=llm, context_builder=builder)

    task = AgentTask(
        tipo=TaskType.GENERATE_CODE,
        descripcion="Genera una nueva función",
        input_context={"instruction": "Genera nueva_funcion", "file_path": "app.py"},
    )
    result = tool.execute(task, ContextBundle(files=files))
    assert result.success
    assert len(result.patches) == 1
    assert "nueva_funcion" in result.patches[0].new_content


# ---------------------------------------------------------------------------
# DocGeneratorTool
# ---------------------------------------------------------------------------

def test_doc_generator_explains_code():
    llm = LLMClient(provider=MockLLMProvider("Esta función suma dos números enteros."))
    files = [CodeFile(path="calc.py", content=SAMPLE_PYTHON, language="python")]
    index = CodebaseIndex(files=files)
    builder = ContextBuilder(index=index)
    tool = DocGeneratorTool(llm=llm, context_builder=builder)

    task = AgentTask(
        tipo=TaskType.EXPLAIN_CODE,
        descripcion="Explica la función suma",
        input_context={"question": "¿Qué hace suma?"},
    )
    result = tool.execute(task, ContextBundle(files=files))
    assert result.success
    assert len(result.output) > 0


# ---------------------------------------------------------------------------
# Intent classification (indirectamente via can_handle)
# ---------------------------------------------------------------------------

def test_tools_can_handle_correct_tasks():
    llm = LLMClient(provider=MockLLMProvider())
    index = CodebaseIndex()
    builder = ContextBuilder(index=index)

    gen_tool = CodeGenerationTool(llm=llm, context_builder=builder)
    doc_tool = DocGeneratorTool(llm=llm, context_builder=builder)
    analyzer = CodeAnalyzer()

    gen_task = AgentTask(tipo=TaskType.GENERATE_CODE, descripcion="test")
    refactor_task = AgentTask(tipo=TaskType.REFACTOR_CODE, descripcion="test")
    explain_task = AgentTask(tipo=TaskType.EXPLAIN_CODE, descripcion="test")
    explore_task = AgentTask(tipo=TaskType.EXPLORE_CODEBASE, descripcion="test")

    assert gen_tool.can_handle(gen_task)
    assert gen_tool.can_handle(refactor_task)
    assert not gen_tool.can_handle(explain_task)

    assert doc_tool.can_handle(explain_task)
    assert not doc_tool.can_handle(gen_task)

    assert analyzer.can_handle(explore_task)
    assert not analyzer.can_handle(gen_task)
