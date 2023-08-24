"""
Cooldown system.
"""

import time
from typing import Any


class false:

    def __init__(self, r_a):
        self.retry_after = r_a

    def __bool__(self) -> bool:
        return False


class NewCooldown:
    """
    Creates a new cooldown. Equivalent Javascript:
    ```js
    const cdown = new Cooldown();
    ```

    :param int rate: The rate, or, how many times the user can use the command per [second].
    :param int per: Per second.
    """

    def __init__(self, rate: int, per: float):
        self.cds = {}
        self.rate = rate
        self.per = per

    def __call__(self, target: Any):
        """
        Check or register a cooldown for a user.

        :returns bool:
        """
        if not target in self.cds:
            self.cds[target] = {
                "used": 0,
                "last":
                0,  # so that time.time() - (last := 0) = time.time() >= time.time()
            }

        if target >= self.rate:
            if (ts := time.time()) - self.cds[target]["last"] >= self.per:
                self.cds[target]["last"] = ts
                self.cds[target]["used"] = 1
                return True

            return false((self.cds[target]["last"] + self.per) - ts)

        self.cds[target]["used"] += 1
