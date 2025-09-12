import pytest

from src.tools.rag_tools import InfinitePayRAGTool


class FakeEmbeddings:
    def encode(self, items):
        return [[0.1, 0.2, 0.3]]


class FakeCollection:
    def __init__(self, docs):
        self._docs = docs

    def query(self, query_embeddings, n_results=5, include=None):
        return {
            "documents": [self._docs],
            "metadatas": [[{"source": "fake"} for _ in self._docs]],
            "distances": [[0.1 for _ in self._docs]],
        }


def test_rag_tool_instantiation_calls_setup(monkeypatch):
    called = {"v": False}

    def fake_setup(self):
        called["v"] = True
        self.client = object()
        self.embeddings = FakeEmbeddings()
        self.collection = FakeCollection(["A", "B"])  # minimal

    monkeypatch.setattr(InfinitePayRAGTool, "_setup_vector_store", fake_setup)
    tool = InfinitePayRAGTool()
    assert called["v"] is True
    assert tool.embeddings is not None
    assert tool.collection is not None


def test_rag_tool_run_formats_results(monkeypatch):
    def fake_setup(self):
        self.client = object()
        self.embeddings = FakeEmbeddings()
        self.collection = FakeCollection(["Doc1", "Doc2"])

    monkeypatch.setattr(InfinitePayRAGTool, "_setup_vector_store", fake_setup)
    tool = InfinitePayRAGTool()

    out = tool._run("maquininha InfinitePay")
    assert "Informações encontradas" in out
    assert "Doc1" in out and "Doc2" in out


def test_rag_tool_run_handles_no_results(monkeypatch):
    def fake_setup(self):
        self.client = object()
        self.embeddings = FakeEmbeddings()
        self.collection = FakeCollection([])

    monkeypatch.setattr(InfinitePayRAGTool, "_setup_vector_store", fake_setup)
    tool = InfinitePayRAGTool()

    out = tool._run("pix taxas")
    assert "Não encontrei informações" in out


def test_rag_tool_run_handles_exception(monkeypatch):
    class BoomCollection(FakeCollection):
        def query(self, *args, **kwargs):
            raise RuntimeError("boom")

    def fake_setup(self):
        self.client = object()
        self.embeddings = FakeEmbeddings()
        self.collection = BoomCollection(["irrelevant"])

    monkeypatch.setattr(InfinitePayRAGTool, "_setup_vector_store", fake_setup)
    tool = InfinitePayRAGTool()

    out = tool._run("qualquer")
    assert "Erro na busca RAG" in out
