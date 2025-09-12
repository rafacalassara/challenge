from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

class WebSearchInput(BaseModel):
    query: str = Field(description="Consulta para busca web")
    max_results: int = Field(default=5, description="Número máximo de resultados")


class WebSearchTool(BaseTool):
    name: str = "WebSearch"
    description: str = "Busca informações na web usando DuckDuckGo"
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str, max_results: int) -> str:
        try:
            from duckduckgo_search import DDGS  # type: ignore
        except Exception:
            return (
                "Busca web indisponível neste ambiente (dependência ausente). "
                "Descreva melhor sua pergunta ou tente novamente mais tarde."
            )

        try:
            ddgs = DDGS()
            results = ddgs.text(keywords=query, max_results=max_results)

            # Lazy import for optional dependencies
            try:
                import requests  # type: ignore
                from bs4 import BeautifulSoup  # type: ignore
            except Exception:
                requests = None  # type: ignore
                BeautifulSoup = None  # type: ignore

            def extract_page_text(url: str) -> str:
                if not url:
                    return "(Sem URL para extrair conteúdo)"
                if requests is None or BeautifulSoup is None:  # type: ignore
                    return (
                        "(Extração desabilitada: dependências ausentes. "
                        "Conteúdo limitado ao resumo do resultado.)"
                    )
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    }
                    resp = requests.get(url, timeout=10, headers=headers)  # type: ignore
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "html.parser")  # type: ignore
                    for tag in soup(["script", "style", "noscript"]):
                        tag.extract()
                    text = " ".join(soup.get_text(" ").split())
                    if not text:
                        return "(Sem conteúdo textual visível nesta página)"
                    
                    return text
                except Exception:
                    return "(Falha ao extrair conteúdo desta página)"

            lines = [f"Resultados para '{query}':\n"]
            for i, r in enumerate(results, 1):
                title = r.get("title", "Sem título")
                url = r.get("href", "")
                preview = r.get("body", "Sem descrição")
                page_text = extract_page_text(url)

                lines.append(f"{i}. {title}")
                if url:
                    lines.append(f"   URL: {url}")
                if preview:
                    lines.append(f"   Prévia: {preview[:300]}...")
                lines.append("   Conteúdo extraído:")
                for chunk in page_text.splitlines():
                    chunk = chunk.strip()
                    if chunk:
                        lines.append(f"     {chunk}")
                lines.append("")

            return "\n".join(lines).strip() or "Nenhum resultado encontrado."
        except Exception as e:
            return f"Erro na busca web: {str(e)}"


if __name__ == "__main__":
    tool = WebSearchTool()
    print(tool.run("Qual é o melhor time de futebol do mundo?", max_results=5))
    