"""Time source. Injected so the workflow is testable without sleeping or patching."""

import time
from datetime import UTC, datetime


class SystemClock:
    def now(self) -> datetime:
        """Timezone-aware UTC wall-clock time, for timestamps."""
        return datetime.now(UTC)

    def monotonic(self) -> float:
        """Seconds from a monotonic clock, for measuring durations."""
        return time.monotonic()
