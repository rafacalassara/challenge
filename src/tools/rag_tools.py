from typing import Type, Optional
from pydantic import BaseModel, Field

from crewai.tools import BaseTool
# Optional heavy dependencies are guarded to avoid import errors in light environments
try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover - graceful fallback
    SentenceTransformer = None  # type: ignore

class RAGInput(BaseModel):
    query: str = Field(description="Consulta para buscar na base de conhecimento")


class InfinitePayRAGTool(BaseTool):
    name: str = "InfinitePayRAG"
    description: str = "Busca informações na base de conhecimento InfinitePay"
    args_schema: Type[BaseModel] = RAGInput

    # Lazy-initialized components
    client: Optional[object] = None
    embeddings: Optional[object] = None
    collection: Optional[object] = None

    def __init__(self):
        super().__init__()
        # Try to set up vector store; allow tests to monkeypatch this safely
        try:
            self._setup_vector_store()
        except Exception as e:
            # In environments without heavy deps, allow manual setup in tests
            self.embeddings = None
            self.collection = None

    def _setup_vector_store(self):
        """Setup do vector store com dados InfinitePay"""
        # chromadb is optional; if unavailable, disable RAG gracefully
        try:
            import chromadb  # type: ignore
            from chromadb.errors import InvalidCollectionException  # type: ignore
        except Exception:
            self.client = None
            self.embeddings = None
            self.collection = None
            return

        # sentence-transformers may be unavailable in constrained environments
        if SentenceTransformer is None:
            self.client = None
            self.embeddings = None
            self.collection = None
            return

        self.client = chromadb.PersistentClient(path="./data/vector_store")
        self.embeddings = SentenceTransformer('all-MiniLM-L6-v2')

        try:
            self.collection = self.client.get_collection("infinitepay_kb")
        except (ValueError, InvalidCollectionException):
            self.collection = self.client.create_collection("infinitepay_kb")
            self._index_infinitepay_data()

    def _run(self, query: str) -> str:
        """Executa busca RAG"""
        try:
            if self.client is None or self.embeddings is None or self.collection is None:
                # If not initialized (e.g., tests), signal graceful message
                return "Não encontrei informações específicas na base de conhecimento InfinitePay."

            raw_embedding = self.embeddings.encode([query])
            # Support numpy arrays or native Python lists
            query_embedding = raw_embedding.tolist() if hasattr(raw_embedding, "tolist") else raw_embedding
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=5,
                include=["documents", "metadatas", "distances"],
            )

            documents = results.get("documents") or []
            # documents is typically a list of lists: [[doc1, doc2, ...]]
            docs = documents[0] if documents else []
            if not docs:
                return "Não encontrei informações específicas na base de conhecimento InfinitePay."

            context = "\n".join(docs)
            return f"Informações encontradas na base InfinitePay:\n{context}"

        except Exception as e:
            return f"Erro na busca RAG: {str(e)}"

    def _index_infinitepay_data(self):
        """Indexa dados das URLs InfinitePay.
        Tenta fazer scraping leve; se indisponível, indexa documentos estáticos mínimos.
        """
        urls = [
            "https://www.infinitepay.io",
            "https://www.infinitepay.io/maquininha",
            "https://www.infinitepay.io/pix",
            "https://www.infinitepay.io/maquininha-celular",
            "https://www.infinitepay.io/tap-to-pay",
            "https://www.infinitepay.io/pdv",
            "https://www.infinitepay.io/receba-na-hora",
            "https://www.infinitepay.io/gestao-de-cobranca",
            "https://www.infinitepay.io/gestao-de-cobranca-2",
            "https://www.infinitepay.io/link-de-pagamento",
            "https://www.infinitepay.io/loja-online",
            "https://www.infinitepay.io/boleto",
            "https://www.infinitepay.io/conta-digital",
            "https://www.infinitepay.io/conta-pj",
            "https://www.infinitepay.io/pix",
            "https://www.infinitepay.io/pix-parcelado",
            "https://www.infinitepay.io/emprestimo",
            "https://www.infinitepay.io/cartao",
            "https://www.infinitepay.io/rendimento",
        ]

        docs = []
        metadatas = []
        ids = []

        # Attempt to scrape if requests/bs4 available
        try:
            import requests  # type: ignore
            from bs4 import BeautifulSoup  # type: ignore

            for i, url in enumerate(urls, start=1):
                try:
                    resp = requests.get(url, timeout=10)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Extract visible text
                    for script in soup(["script", "style", "noscript"]):
                        script.extract()
                    text = " ".join(soup.get_text(" ").split())
                    if not text:
                        continue

                    # Chunk text into ~700-char chunks
                    chunk_size = 700
                    for j in range(0, len(text), chunk_size):
                        chunk = text[j : j + chunk_size]
                        docs.append(chunk)
                        metadatas.append({"source": url})
                        ids.append(f"doc-{i}-{j//chunk_size}")
                except Exception:
                    # Skip URL on failure
                    continue

        except Exception:
            # Fallback to static minimal documents
            fallback = [
                "A InfinitePay oferece maquininhas com taxas competitivas e suporte ao PIX.",
                "A conta digital InfinitePay permite pagamentos, cartões e rendimento.",
                "O PIX da InfinitePay facilita recebimentos rápidos para seu negócio.",
            ]
            for k, txt in enumerate(fallback, start=1):
                docs.append(txt)
                metadatas.append({"source": "fallback"})
                ids.append(f"static-{k}")

        if not docs:
            # Ensure at least one doc
            docs = ["Informações gerais sobre InfinitePay e seus produtos (fallback)."]
            metadatas = [{"source": "fallback"}]
            ids = ["static-0"]

        # Embed and add to collection
        try:
            embeddings = self.embeddings.encode(docs).tolist()  # type: ignore[attr-defined]
            self.collection.add(documents=docs, metadatas=metadatas, ids=ids, embeddings=embeddings)  # type: ignore[attr-defined]
        except Exception:
            # If embedding fails, try without embeddings (if collection has embedding function)
            try:
                self.collection.add(documents=docs, metadatas=metadatas, ids=ids)  # type: ignore[attr-defined]
            except Exception:
                # Last resort: ignore indexing errors silently to avoid breaking init
                return

if __name__ == "__main__":
    print(InfinitePayRAGTool().name)
    # tool = InfinitePayRAGTool()
    # tool._index_infinitepay_data()