from pathlib import Path
from langchain.globals import set_llm_cache
from langchain_community.cache import InMemoryCache, SQLiteCache

CACHE_DIR = Path("data")
CACHE_DIR.mkdir(exist_ok=True)

def configure_cache(cache_type="SQLiteCache"):
    """Register one global LangChain cache backend."""
    if cache_type == "InMemoryCache":
        set_llm_cache(InMemoryCache())
    elif cache_type == "SQLiteCache":
        set_llm_cache(SQLiteCache(database_path=str(CACHE_DIR / "llm_cache.db")))
    else:
        set_llm_cache(None)
