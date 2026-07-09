"""Document loader — reads PDFs and text files into LangChain Documents."""

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document


def load_document(file_path: str | Path) -> list[Document]:
    """Load a document from disk and return a list of LangChain Documents.

    Supports PDF (.pdf) and plain text (.txt, .md) files.

    Args:
        file_path: Path to the file to load.

    Returns:
        List of Document objects with page_content and metadata.

    Raises:
        ValueError: If the file type is not supported.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        loader = PyPDFLoader(str(path))
        documents = loader.load()
    elif suffix in {".txt", ".md", ".rst"}:
        loader = TextLoader(str(path), encoding="utf-8")
        documents = loader.load()
    else:
        raise ValueError(
            f"Unsupported file type: {suffix}. Supported types: .pdf, .txt, .md, .rst"
        )

    # Enrich metadata with the source filename
    for doc in documents:
        doc.metadata["source_filename"] = path.name
        doc.metadata["file_type"] = suffix

    return documents
