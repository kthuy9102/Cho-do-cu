"""Giới hạn đăng nhập sai (chống dò mật khẩu): tối đa N lần sai / cửa sổ thời gian cho mỗi (IP, email).
Lưu trong bộ nhớ tiến trình -> đủ cho 1 worker; nhiều worker cần Redis (xem README)."""
import threading
import time
from collections import defaultdict, deque

from app.core.exceptions import TooManyRequestsError


class LoginThrottle:
    def __init__(self, max_failures: int = 5, window_seconds: int = 900) -> None:
        self.max_failures = max_failures
        self.window = window_seconds
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, q: deque[float], now: float) -> None:
        while q and now - q[0] > self.window:
            q.popleft()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            q = self._failures.get(key)
            if not q:
                return
            self._prune(q, now)
            if not q:
                del self._failures[key]
            elif len(q) >= self.max_failures:
                retry_after = int(self.window - (now - q[0])) + 1
                raise TooManyRequestsError(
                    "Đăng nhập sai quá nhiều lần, vui lòng thử lại sau",
                    code="too_many_attempts",
                    headers={"Retry-After": str(retry_after)},
                )

    def record_failure(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            if len(self._failures) > 10_000:  # tránh phình bộ nhớ khi bị quét email ngẫu nhiên
                for k in [k for k, q in self._failures.items() if not q or now - q[-1] > self.window]:
                    del self._failures[k]
            q = self._failures[key]
            self._prune(q, now)
            q.append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)


login_throttle = LoginThrottle()
