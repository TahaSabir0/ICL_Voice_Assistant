"""
Subprocess-based RAG retriever for Qt UI compatibility.

ChromaDB / sentence-transformers / ONNX Runtime cause native segfaults when
called from a QThread because their internal thread pools conflict with Qt's
event loop. This module runs all RAG operations in a separate process,
communicating via multiprocessing.Pipe.

Usage:
    retriever = SubprocessRetriever()
    retriever.start()  # Spawns child process, loads models
    context = retriever.get_context("What is 3D printing?")
    retriever.stop()
"""

import multiprocessing
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# Messages sent from parent -> child
@dataclass
class _Request:
    type: str  # "init", "get_context", "search", "shutdown"
    query: str = ""
    n_results: int = 3
    max_context_length: int = 4000
    relevance_threshold: float = 0.3
    store_path: str = ""


# Messages sent from child -> parent
@dataclass
class _Response:
    success: bool
    data: str = ""  # context string or error message
    doc_count: int = 0


def _worker_process(conn, store_path: str, relevance_threshold: float):
    """
    Child process entry point. Runs the actual Retriever in isolation.

    This function runs in its own process with its own Python interpreter,
    so ONNX Runtime and SQLite are completely isolated from Qt.
    """
    retriever = None

    try:
        # Import here — these imports happen in the child process only
        from src.rag.retriever import Retriever

        store_path_obj = Path(store_path) if store_path else None
        retriever = Retriever(
            store_path=store_path_obj,
            relevance_threshold=relevance_threshold
        )

        # Preload embedding model
        _ = retriever.store.embedding_service.model

        doc_count = retriever.store.count()
        conn.send(_Response(success=True, doc_count=doc_count))

    except Exception as e:
        conn.send(_Response(success=False, data=f"Init failed: {e}"))
        conn.close()
        return

    # Message loop
    while True:
        try:
            if not conn.poll(timeout=1.0):
                continue

            request = conn.recv()

            if request.type == "shutdown":
                conn.send(_Response(success=True, data="shutdown"))
                break

            elif request.type == "get_context":
                try:
                    context = retriever.get_context(
                        request.query,
                        n_results=request.n_results,
                        max_context_length=request.max_context_length
                    )
                    conn.send(_Response(success=True, data=context))
                except Exception as e:
                    conn.send(_Response(success=False, data=f"Query error: {e}"))

            else:
                conn.send(_Response(success=False, data=f"Unknown request: {request.type}"))

        except EOFError:
            # Parent closed the connection
            break
        except Exception as e:
            try:
                conn.send(_Response(success=False, data=f"Worker error: {e}"))
            except Exception:
                break

    conn.close()


class SubprocessRetriever:
    """
    RAG retriever that runs in a subprocess to avoid Qt/ONNX conflicts.

    Drop-in replacement for Retriever.get_context() that is safe to call
    from any thread, including QThreads.
    """

    def __init__(
        self,
        store_path: Optional[Path] = None,
        relevance_threshold: float = 0.3,
        timeout: float = 30.0
    ):
        from src.rag.vectorstore import DEFAULT_STORE_PATH
        self.store_path = str(store_path or DEFAULT_STORE_PATH)
        self.relevance_threshold = relevance_threshold
        self.timeout = timeout

        self._process: Optional[multiprocessing.Process] = None
        self._conn = None  # Parent side of the Pipe
        self._doc_count = 0
        self._is_ready = False

    @property
    def is_ready(self) -> bool:
        return self._is_ready and self._process is not None and self._process.is_alive()

    @property
    def doc_count(self) -> int:
        return self._doc_count

    def start(self, progress_callback=None) -> bool:
        """
        Start the subprocess and initialize the retriever.

        Returns True if initialization succeeded.
        """
        if self._process is not None:
            self.stop()

        parent_conn, child_conn = multiprocessing.Pipe()
        self._conn = parent_conn

        self._process = multiprocessing.Process(
            target=_worker_process,
            args=(child_conn, self.store_path, self.relevance_threshold),
            daemon=True,
            name="rag-subprocess"
        )
        self._process.start()

        # Wait for init response
        if progress_callback:
            progress_callback("Loading RAG in subprocess...")

        try:
            if self._conn.poll(timeout=120):  # Models can take a while to load
                response = self._conn.recv()
                if response.success:
                    self._doc_count = response.doc_count
                    self._is_ready = True
                    if progress_callback:
                        progress_callback(f"  RAG ready: {self._doc_count} documents")
                    return True
                else:
                    print(f"RAG subprocess init failed: {response.data}")
                    self.stop()
                    return False
            else:
                print("RAG subprocess timed out during initialization")
                self.stop()
                return False
        except Exception as e:
            print(f"RAG subprocess error: {e}")
            self.stop()
            return False

    def get_context(
        self,
        query: str,
        n_results: int = 3,
        max_context_length: int = 4000
    ) -> str:
        """
        Get RAG context for a query. Safe to call from any thread.

        Returns empty string if retriever is not ready or on error.
        """
        if not self.is_ready:
            return ""

        try:
            self._conn.send(_Request(
                type="get_context",
                query=query,
                n_results=n_results,
                max_context_length=max_context_length
            ))

            if self._conn.poll(timeout=self.timeout):
                response = self._conn.recv()
                if response.success:
                    return response.data
                else:
                    print(f"RAG query error: {response.data}")
                    return ""
            else:
                print("RAG query timed out")
                return ""

        except Exception as e:
            print(f"RAG communication error: {e}")
            self._is_ready = False
            return ""

    def stop(self):
        """Stop the subprocess."""
        self._is_ready = False

        if self._conn is not None:
            try:
                self._conn.send(_Request(type="shutdown"))
            except Exception:
                pass
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

        if self._process is not None:
            self._process.join(timeout=5)
            if self._process.is_alive():
                self._process.kill()
            self._process = None
