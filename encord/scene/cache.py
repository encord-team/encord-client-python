"""Point cloud caching utilities.

This module provides caching functionality for point cloud files to avoid
repeated downloads of the same data.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests


class PointCloudCache:
    """Cache for point cloud files.

    Caches downloaded point cloud files locally to avoid repeated downloads.
    Files are stored in ~/.encord-client-python/scene/cache by default.

    Example:
        >>> cache = PointCloudCache()
        >>> content = cache.download(url)  # Downloads and caches
        >>> content = cache.download(url)  # Returns from cache
        >>> print(f"Cache size: {cache.size / 1024 / 1024:.2f} MB")
        >>> cache.clear()  # Clear all cached files
    """

    DEFAULT_CACHE_DIR = Path.home() / ".encord-client-python" / "scene" / "cache"

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the cache.

        Args:
            cache_dir: Custom cache directory. If None, uses the default
                (~/.encord-client-python/scene/cache).
        """
        self._cache_dir = cache_dir or self.DEFAULT_CACHE_DIR

    @property
    def dir(self) -> Path:
        """Get the cache directory path, creating it if necessary."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        return self._cache_dir

    @property
    def size(self) -> int:
        """Get the total size of cached files in bytes."""
        if not self._cache_dir.exists():
            return 0
        return sum(f.stat().st_size for f in self._cache_dir.iterdir() if f.is_file())

    @property
    def file_count(self) -> int:
        """Get the number of cached files."""
        if not self._cache_dir.exists():
            return 0
        return sum(1 for f in self._cache_dir.iterdir() if f.is_file())

    def get_cache_key(self, url: str) -> str:
        """Generate a cache key from a URL.

        Extracts a stable identifier from the URL path, ignoring query parameters
        (which contain signed URL tokens that change).

        Args:
            url: The full URL including query parameters.

        Returns:
            A hash-based cache key.
        """
        parsed = urlparse(url)
        # Use the path portion only (ignoring query params which contain tokens)
        # Hash the path to create a safe filename
        path_hash = hashlib.sha256(parsed.path.encode()).hexdigest()[:16]

        # Try to extract a meaningful filename from the path
        path_parts = parsed.path.rstrip("/").split("/")
        filename = path_parts[-1] if path_parts else "unknown"

        # Sanitize filename
        safe_filename = "".join(c if c.isalnum() or c in ".-_" else "_" for c in filename)

        return f"{safe_filename}_{path_hash}"

    def get(self, url: str) -> Optional[bytes]:
        """Get cached file content if it exists.

        Args:
            url: The URL that was used to download the file.

        Returns:
            The cached file content, or None if not cached.
        """
        cache_key = self.get_cache_key(url)
        cache_path = self.dir / cache_key

        if cache_path.exists():
            return cache_path.read_bytes()
        return None

    def put(self, url: str, content: bytes) -> Path:
        """Save content to the cache.

        Args:
            url: The URL that was used to download the file.
            content: The file content to cache.

        Returns:
            The path where the file was cached.
        """
        cache_key = self.get_cache_key(url)
        cache_path = self.dir / cache_key
        cache_path.write_bytes(content)
        return cache_path

    def has(self, url: str) -> bool:
        """Check if a URL is cached.

        Args:
            url: The URL to check.

        Returns:
            True if the URL is cached, False otherwise.
        """
        cache_key = self.get_cache_key(url)
        cache_path = self.dir / cache_key
        return cache_path.exists()

    def download(self, url: str, timeout: float = 30.0, cache_key: Optional[str] = None) -> bytes:
        """Download a file, using cache if available.

        Args:
            url: The URL to download from (may be a signed URL).
            timeout: Download timeout in seconds.
            cache_key: The key to use for caching (e.g., stable/unsigned URL).
                If None, uses the download URL as the key.

        Returns:
            The file content.
        """
        key = cache_key or url
        cached = self.get(key)
        if cached is not None:
            return cached

        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        content = response.content

        self.put(key, content)
        return content

    async def download_async(self, url: str, timeout: float = 30.0, cache_key: Optional[str] = None) -> bytes:
        """Download a file asynchronously, using cache if available.

        Args:
            url: The URL to download from (may be a signed URL).
            timeout: Download timeout in seconds.
            cache_key: The key to use for caching (e.g., stable/unsigned URL).
                If None, uses the download URL as the key.

        Returns:
            The file content.
        """
        key = cache_key or url
        cached = self.get(key)
        if cached is not None:
            return cached

        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp is required for async downloads. Install it with: pip install aiohttp")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                response.raise_for_status()
                content = await response.read()

        self.put(key, content)
        return content

    def clear(self) -> int:
        """Clear all cached files.

        Returns:
            The number of files deleted.
        """
        if not self._cache_dir.exists():
            return 0

        count = 0
        for file in self._cache_dir.iterdir():
            if file.is_file():
                file.unlink()
                count += 1
        return count

    def __repr__(self) -> str:
        return f"PointCloudCache(dir={self._cache_dir!r}, files={self.file_count}, size={self.size})"


# Default cache instance
_default_cache: Optional[PointCloudCache] = None


def get_default_cache() -> PointCloudCache:
    """Get the default cache instance.

    Returns:
        The default PointCloudCache instance.
    """
    global _default_cache
    if _default_cache is None:
        _default_cache = PointCloudCache()
    return _default_cache


# Convenience functions that use the default cache
def get_cache_dir() -> Path:
    """Get the default cache directory path."""
    return get_default_cache().dir


def get_cache_size() -> int:
    """Get the total size of cached files in bytes."""
    return get_default_cache().size


def clear_cache() -> int:
    """Clear all cached files from the default cache."""
    return get_default_cache().clear()
