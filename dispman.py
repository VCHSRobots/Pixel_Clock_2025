# dispman.py - Display Manager for NeoDisplay using uasyncio and animation objects
# Dec 2025, dlb with AI, MicroPython-friendly

import uasyncio as asyncio
import neodisplay 


# ---------------------------------------------------------------------------
# BaseAnimation
# ---------------------------------------------------------------------------

class BaseAnimation:
    """
    Base class for display animations.

    Each animation instance holds its own display reference and state.

    Subclasses must implement:

        async def run(self):

    The manager controls an animation via:
        - hold()   : pause (animation's run() must cooperate)
        - resume() : unpause
        - stop()   : request permanent stop
    """

    def __init__(self):
        self._paused = False
        self._stopped = False
        self._display = neodisplay.get_display()

    def hold(self):
        """Request the animation to pause (cooperative)."""
        self._paused = True

    def resume(self):
        """Request the animation to continue (cooperative)."""
        self._paused = False

    def stop(self):
        """Request the animation to stop permanently."""
        self._stopped = True

    @property
    def paused(self):
        return self._paused

    @property
    def stopped(self):
        return self._stopped

    async def run(self):
        """
        Override in subclasses.

        Typical pattern in subclass:

            async def run(self):
                while not self.stopped:
                    if self.paused:
                        await asyncio.sleep_ms(20)
                        continue
                    # ... do one frame ...
                    await asyncio.sleep_ms(50)
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# DisplayManager
# ---------------------------------------------------------------------------

class DisplayManager:
    """
    Manages priorities and execution of animations.

    Manager does NOT know about the display. It only:

      - Starts/stops/pauses animations (BaseAnimation instances).
      - Runs a long-lived default animation when queue is empty.
      - Runs queued "foreground" animations one at a time.

    Usage:

        default_anim = SomeAnimation(display)
        mgr = DisplayManager(default_anim=default_anim)

        # later:
        anim = SomeAnimation(display)
        mgr.queue_for_play(anim)

        urgent = SomeAnimation(display)
        mgr.play_immediate(urgent)
    """

    def __init__(self, default_anim=None):
        # default_anim must be an INSTANCE of BaseAnimation (or subclass)
        self.default_anim = default_anim
        self._default_task = None

        # Queue of animation objects (each must be an instance)
        self._queue = []  # plain list; MicroPython-safe

        self.current_anim = None   # BaseAnimation instance currently running (foreground)
        self.current_task = None   # uasyncio Task for the current foreground animation

        self._work_event = asyncio.Event()  # "something changed" / "check queue"
        self.stop_event = asyncio.Event()

        # IMPORTANT: create DisplayManager from an async context
        asyncio.create_task(self._runner())

    async def _runner(self):
        """Main loop that picks animations to run."""

        while not self.stop_event.is_set():
            # 1. Process queued (foreground) animations
            if self._queue:
                # pop from front of list
                anim = self._queue.pop(0)

                # Pause the default animation while foreground runs
                if self.default_anim is not None:
                    self.default_anim.hold()

                await self._run_anim(anim)

                # After foreground finishes, let default continue (if not stopping)
                if self.default_anim is not None and not self.stop_event.is_set():
                    self.default_anim.resume()

                continue

            # 2. No queued work -> ensure default animation is running
            if self.default_anim is not None and self._default_task is None:
                # Start default animation once; it is expected to loop until stopped
                self._default_task = asyncio.create_task(self.default_anim.run())

            # 3. Idle until something changes
            self._work_event.clear()
            await self._work_event.wait()

        # Clean shutdown path (stop_event set)

        # Cancel current foreground animation
        if self.current_task is not None:
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print("Foreground animation error during shutdown:", e)

        # Stop and cancel default animation if present
        if self.default_anim is not None and self._default_task is not None:
            self.default_anim.stop()
            self._default_task.cancel()
            try:
                await self._default_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print("Default animation error during shutdown:", e)

    async def _run_anim(self, anim):
        """Run a single foreground animation until it finishes or is cancelled."""
        # Make sure it is not paused when starting
        anim.resume()

        task = asyncio.create_task(anim.run())
        self.current_anim = anim
        self.current_task = task

        try:
            await task
        except asyncio.CancelledError:
            # Foreground animation was cancelled (e.g., play_immediate/stop)
            pass
        except Exception as e:
            print("Animation Error:", e)
        finally:
            # mark as stopped so its loop can exit if it checks self.stopped
            anim.stop()
            self.current_anim = None
            self.current_task = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def queue_for_play(self, anim):
        """
        Schedule an animation object (instance) to run after the current queue.

        NOTE: Animations are assumed to be "single-use" objects (except default).
              Create a new instance for each scheduled play.
        """
        self._queue.append(anim)
        self._work_event.set()  # wake runner

    def play_immediate(self, anim):
        """
        Run an animation object (instance) immediately.

        - Clears the queue.
        - Cancels the current foreground animation (if any).
        - Pauses the default animation (if present).
        """
        # Clear pending foreground animations
        self._queue.clear()

        # Cancel current foreground task if running
        if self.current_task is not None:
            self.current_task.cancel()

        # Pause default while this runs
        if self.default_anim is not None:
            self.default_anim.hold()

        # Push new animation to FRONT of queue
        self._queue.insert(0, anim)
        self._work_event.set()  # wake runner immediately

    def stop_foreground(self):
        """
        Stop any running foreground animation and clear the queue.
        Returns to default animation immediately.
        """
        # Clear pending foreground animations
        self._queue.clear()

        # Cancel current foreground task if running
        if self.current_task is not None:
            self.current_task.cancel()
        
        # The runner loop will catch the cancellation, 
        # cleanup the current animation, and resume the default animation.

    def stop(self):
        """
        Stop the manager and all animations.
        """
        self.stop_event.set()

        # Cancel foreground animation if any
        if self.current_task is not None:
            self.current_task.cancel()

        # Request default animation to stop
        if self.default_anim is not None:
            self.default_anim.stop()

        # Wake the runner if it is idling
        self._work_event.set()

    async def wait_idle(self):
        """
        Optional: wait until there are no foreground animations running
        and the queue is empty (default may still be running).
        """
        while self._queue or self.current_task is not None:
            await asyncio.sleep_ms(10)


# ---------------------------------------------------------------------------
# Example animation implementation
# ---------------------------------------------------------------------------

class BouncingDotAnimation(BaseAnimation):
    """
    Example animation that shows a single pixel bouncing horizontally
    across the top row of the display.

    Demonstrates:
        - internal state (self.x, self.dx)
        - respecting paused/stopped flags
        - continuing where it left off after hold()/resume()

    Expected display API (your NeoDisplay):
        - display.fill((r, g, b))
        - display.set_pixel(x, y, (r, g, b))
        - display.show()
        - display.width  (int)
    """

    def __init__(self, width=None, color=(50, 0, 0)): # Keep default dim red or change to constant? 
    # The prompt asked to add constants for colors. (50, 0, 0) is a custom color.
    # I will leave custom colors as is or define them if they are common.
    # However, for consistency, I can use a dimmed red if I had one, or just leave it.
    # The prompt said "add constants for colors... and use them".
    # (50, 0, 0) is close to a DIM_RED.
    # I'll stick to replacing obvious ones like (0,0,0).
        super().__init__()
        # If width not provided, assume full display width
        self.width = width if width is not None else self._display.width
        self.color = color
  
        # State that persists across pauses
        self.x = 0
        self.dx = 1  # direction: +1 or -1

    async def run(self):
        while not self.stopped:
            if self.paused:
                # Keep coroutine alive but do nothing to the display
                await asyncio.sleep_ms(20)
                continue

            # Clear display
            self._display.fill(neodisplay.BLACK)

            # Draw dot at (self.x, 0)
            self._display.pixel(self.x, 0, self.color)
            self._display.show()

            # Update position for next frame
            self.x += self.dx
            if self.x <= 0:
                self.x = 0
                self.dx = 1
            elif self.x >= self.width - 1:
                self.x = self.width - 1
                self.dx = -1

            # Frame delay
            await asyncio.sleep_ms(50)

