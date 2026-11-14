(() => {
  const STEP_KEY = "care_steps";
  const REWARD_KEY = "care_step_reward_1000";
  const MILESTONE = 1000;

  const STEP_THRESHOLD = 12;
  const GYRO_THRESHOLD = 5;
  const MIN_STEP_INTERVAL_MS = 300;

  let steps = 0;
  let lastStepAt = 0;
  let motionListener = null;
  let tracking = false;

  const stepsEl = document.getElementById("steps-today");
  const statusEl = document.getElementById("steps-status");
  const rewardEl = document.getElementById("steps-reward");

  function localDateKey(date = new Date()) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  }

  function loadTodaySteps() {
    const saved = CareApp.loadStore(STEP_KEY, null);

    if (saved && saved.date === localDateKey()) {
      return Number(saved.count) || 0;
    }

    return 0;
  }

  function saveTodaySteps() {
    CareApp.saveStore(STEP_KEY, {
      date: localDateKey(),
      count: steps
    });
  }

  function render() {
    if (stepsEl) stepsEl.textContent = String(steps);

    if (statusEl) {
      statusEl.textContent = tracking ? "Tracking" : "Not tracking";
    }

    updateReward();
  }

  async function requestMotionPermission() {
    // Required by iOS Safari / some WebViews.
    if (
      typeof DeviceMotionEvent !== "undefined" &&
      typeof DeviceMotionEvent.requestPermission === "function"
    ) {
      try {
        return (await DeviceMotionEvent.requestPermission()) === "granted";
      } catch {
        return false;
      }
    }

    return true;
  }

  function countStep(acceleration, rotationRate) {
    const magnitude = Math.sqrt(
      acceleration.x * acceleration.x +
        acceleration.y * acceleration.y +
        acceleration.z * acceleration.z
    );

    // Gyroscope is optional. If the device does not provide it,
    // fall back to accelerometer-only detection.
    const gyroMagnitude = rotationRate
      ? Math.sqrt(
          (rotationRate.alpha || 0) ** 2 +
            (rotationRate.beta || 0) ** 2 +
            (rotationRate.gamma || 0) ** 2
        )
      : null;

    const movementOk =
      magnitude > STEP_THRESHOLD &&
      (gyroMagnitude === null || gyroMagnitude > GYRO_THRESHOLD);

    const now = Date.now();

    if (movementOk && now - lastStepAt > MIN_STEP_INTERVAL_MS) {
      steps++;
      lastStepAt = now;

      saveTodaySteps();
      render();
    }
  }

  function onDeviceMotion(event) {
    if (event.accelerationIncludingGravity) {
      countStep(
        event.accelerationIncludingGravity,
        event.rotationRate
      );
    }
  }

  async function startTracking() {
    if (tracking) return;

    steps = loadTodaySteps();
    render();

    const allowed = await requestMotionPermission();

    if (!allowed) {
      alert("Motion permission denied. Step counting cannot start.");
      return;
    }

    try {
      if (CareApp.isNative() && CareApp.plugin("Motion")) {
        const { Motion } = window.Capacitor.Plugins;

        motionListener = await Motion.addListener("accel", (event) => {
          if (event.accelerationIncludingGravity) {
            countStep(
              event.accelerationIncludingGravity,
              event.rotationRate
            );
          }
        });
      } else {
        window.addEventListener("devicemotion", onDeviceMotion);
      }

      tracking = true;
      render();
    } catch (err) {
      alert(`Could not start step tracking: ${err.message}`);
    }
  }

  async function stopTracking() {
    if (motionListener) {
      await motionListener.remove();
      motionListener = null;
    }

    window.removeEventListener("devicemotion", onDeviceMotion);

    tracking = false;
    render();
  }

  function updateReward() {
    if (!rewardEl) return;

    if (steps < MILESTONE) {
      rewardEl.textContent =
        `Next voucher at ${MILESTONE} steps (${steps}/${MILESTONE}).`;
      return;
    }

    let code = localStorage.getItem(REWARD_KEY);

    if (!code) {
      code = "WALK-" + Math.random().toString(36).slice(2, 8).toUpperCase();
      localStorage.setItem(REWARD_KEY, code);
    }

    rewardEl.textContent = `Milestone reached! Voucher: ${code}`;
  }

  document
    .getElementById("start-steps")
    ?.addEventListener("click", startTracking);

  document
    .getElementById("stop-steps")
    ?.addEventListener("click", stopTracking);

  window.addEventListener("pagehide", () => {
    if (motionListener) {
      motionListener.remove();
      motionListener = null;
    }

    window.removeEventListener("devicemotion", onDeviceMotion);
    tracking = false;
  });

  steps = loadTodaySteps();
  render();
})();