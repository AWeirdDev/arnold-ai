"""
Message Editor
"""

import time
import json
import httpx
import asyncio
import discord
from urllib.parse import quote


class Editor:
    """
    Help class for slash command response editing, with rate limit handling.
    """

    f: str
    last: float
    updates: int
    rate_limit: float | int
    rt: float
    too_long: bool

    def __init__(self):
        self.f = ""
        self.last = time.time()
        self.updates = 0
        self.rate_limit = 0
        self.rt = 0  # rate limit timestamp
        self.too_long = False

    async def edit(self, ctx, chunk: str) -> None:
        """
        Edits the response.

        :param ctx: The slash command context.
        :param str chunk: The chunk of text, will be recorded.
        """
        cursor = "\u200B<a:cursor:1117432267749462046>"
        if len(self.f + chunk) > 4090:
            self.too_long = True
            self.f += chunk
            return

        self.f += chunk
        if self.rate_limit:
            return

        try:
            if (ts := time.time()) - self.last >= 5.5:
                if len(self.f) > 1500:
                    await ctx.edit(
                        content="",
                        embed=discord.Embed(
                            description=self.f + cursor, color=0x0995EC
                        ),
                    )
                else:
                    await ctx.edit(content=self.f + cursor)

                self.last = ts
                self.updates += 1
        except discord.HTTPException as error:
            try:
                js = await error.response.json()
                retry_after: float = js["retry_after"]
            except (json.decoder.JSONDecodeError, KeyError):
                self.rate_limit = 10
                self.rt = time.time()
                print("Rate limited, but no wait time specified. (retry in 10s)")
                return

            self.rate_limit = retry_after
            self.rt = time.time()
            print(f"We're being rate limited. (retry in {retry_after}s)")

    async def wait(self):
        """
        Wait for all instances including rate limits without `done`.
        """
        if not self.rate_limit:
            if self.updates:
                await asyncio.sleep((self.last + 5.5) - time.time())
        elif (wait := (self.rt + self.rate_limit) - time.time()) > 0:
            await asyncio.sleep(wait)

    async def done(self, ctx, *args, **kwargs) -> str:
        """
        Finish the session.

        :param ctx: The slash command context.
        """

        await self.wait()

        if len(self.f) > 1500:
            await ctx.edit(
                content="",
                embed=discord.Embed(description=self.f, color=0x0995EC),
                *args,
                **kwargs,
            )
        else:
            await ctx.edit(content=self.f, *args, **kwargs)

        return self.f
