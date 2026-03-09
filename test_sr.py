import sys
import os
import multiprocessing

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    from src.rag.subprocess_retriever import SubprocessRetriever
    print("Initializing retriever...")
    r = SubprocessRetriever()
    success = r.start(progress_callback=print)
    print("Init success:", success)
    if success:
        print("Querying...")
        ctx = r.get_context("what is ICL?")
        print("Got context length:", len(ctx))
    r.stop()
    print("Done")
