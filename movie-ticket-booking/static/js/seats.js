(() => {
  const booking = document.querySelector("[data-seat-booking]");
  if (!booking) return;

  const buttons = [...booking.querySelectorAll(".seat:not(:disabled)")];
  const selected = new Map();
  const initialExpiry = new Map();
  buttons.filter((button) => button.classList.contains("state-mine")).forEach((button) => {
    selected.set(button.dataset.seatId, button);
    initialExpiry.set(button.dataset.seatId, new Date(button.dataset.expiresAt).getTime());
  });
  const selectionLabel = booking.querySelector("[data-selection-label]");
  const selectionTotal = booking.querySelector("[data-selection-total]");
  const timerLabel = booking.querySelector("[data-hold-timer]");
  const continueLink = booking.querySelector("[data-continue]");
  const alertBox = booking.querySelector("[data-seat-alert]");
  let debounce;
  let requestVersion = 0;
  let lastHoldDeadline = 0;
  let serverSynced = selected.size > 0;

  const csrf = () => document.cookie.split(";").map((part) => part.trim()).find((part) => part.startsWith("csrftoken="))?.split("=").slice(1).join("=") || "";
  const seats = () => [...selected.values()];
  const total = () => seats().reduce((sum, seat) => sum + Number(seat.dataset.price), 0);
  const formatMoney = (amount) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(amount);
  const setAlert = (message, kind = "") => {
    alertBox.textContent = message;
    alertBox.className = `seat-alert ${kind}`;
    if (message) window.setTimeout(() => { if (alertBox.textContent === message) alertBox.textContent = ""; }, 5000);
  };
  const paint = () => {
    const picked = seats();
    picked.forEach((seat) => { seat.classList.add("state-mine"); seat.classList.remove("state-available"); });
    booking.querySelectorAll(".seat.state-mine").forEach((seat) => {
      if (!selected.has(seat.dataset.seatId)) { seat.classList.remove("state-mine"); seat.classList.add("state-available"); }
    });
    selectionLabel.textContent = picked.length ? picked.map((seat) => seat.dataset.seatLabel).sort((a, b) => a.localeCompare(b, undefined, { numeric: true })).join(", ") : "No seats selected";
    selectionTotal.textContent = formatMoney(total());
    const canContinue = picked.length > 0 && serverSynced;
    continueLink.classList.toggle("is-disabled", !canContinue);
    continueLink.setAttribute("aria-disabled", canContinue ? "false" : "true");
    continueLink.tabIndex = canContinue ? 0 : -1;
    if (!picked.length) timerLabel.textContent = "Choose seats to begin";
  };
  const refreshTimer = () => {
    const expiryList = seats().map((seat) => initialExpiry.get(seat.dataset.seatId) || lastHoldDeadline).filter(Boolean);
    if (!expiryList.length) return;
    const seconds = Math.max(0, Math.floor((Math.min(...expiryList) - Date.now()) / 1000));
    if (!seconds) {
      timerLabel.textContent = "Hold expired · choose seats again";
      continueLink.classList.add("is-disabled");
      continueLink.setAttribute("aria-disabled", "true");
      return;
    }
    timerLabel.textContent = `Held for you · ${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")} remaining`;
  };

  async function saveSelection(version) {
    try {
      const response = await fetch(booking.dataset.holdUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
        body: JSON.stringify({ seat_ids: seats().map((seat) => Number(seat.dataset.seatId)) }),
      });
      const data = await response.json();
      if (!response.ok) {
        setAlert(data.error || "Unable to reserve those seats. Refresh and try again.", "alert-error");
        window.setTimeout(() => window.location.reload(), 1200);
        return;
      }
      lastHoldDeadline = Date.now() + data.expires_in * 1000;
      selected.forEach((seat, id) => initialExpiry.set(id, lastHoldDeadline));
      if (version !== requestVersion) {
        window.clearTimeout(debounce);
        debounce = window.setTimeout(() => saveSelection(requestVersion), 80);
        return;
      }
      serverSynced = true;
      setAlert(selected.size ? "Your seats are held for five minutes." : "Seat hold released.", "alert-success");
      paint();
      refreshTimer();
    } catch {
      setAlert("Connection issue. Your seat selection could not be saved.", "alert-error");
    }
  }

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const id = button.dataset.seatId;
      if (selected.has(id)) {
        selected.delete(id);
        initialExpiry.delete(id);
      } else {
        if (selected.size >= 10) { setAlert("You can book up to 10 seats in one order.", "alert-error"); return; }
        selected.set(id, button);
      }
      serverSynced = false;
      paint();
      requestVersion += 1;
      window.clearTimeout(debounce);
      debounce = window.setTimeout(() => saveSelection(requestVersion), 180);
    });
  });
  continueLink.addEventListener("click", (event) => {
    if (!selected.size || continueLink.getAttribute("aria-disabled") === "true") event.preventDefault();
  });

  paint();
  refreshTimer();
  window.setInterval(refreshTimer, 1000);
})();
