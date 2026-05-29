document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
        const input = button.parentElement.querySelector("input");

        if (!input) {
            return;
        }

        const shouldShow = input.type === "password";
        input.type = shouldShow ? "text" : "password";
        button.setAttribute("aria-label", shouldShow ? "Hide password" : "Show password");
    });
});

document.querySelectorAll("[data-bs-toggle='collapse']").forEach((button) => {
    button.addEventListener("click", () => {
        const target = document.querySelector(button.getAttribute("data-bs-target"));

        if (!target) {
            return;
        }

        const isOpen = target.classList.toggle("show");
        button.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });
});

document.querySelectorAll("[data-notification-popup]").forEach((popup) => {
    const notificationId = popup.getAttribute("data-notification-id");
    const storageKey = "yuraisha:last-notification-popup";

    function rememberNotification() {
        try {
            localStorage.setItem(storageKey, notificationId);
        } catch (error) {
            return;
        }
    }

    function hidePopup() {
        popup.classList.remove("is-visible");
        window.setTimeout(() => {
            popup.hidden = true;
        }, 220);
    }

    let lastSeenId = null;
    try {
        lastSeenId = localStorage.getItem(storageKey);
    } catch (error) {
        lastSeenId = null;
    }

    if (!notificationId || notificationId === lastSeenId) {
        return;
    }

    popup.hidden = false;
    window.requestAnimationFrame(() => {
        popup.classList.add("is-visible");
    });
    rememberNotification();

    const dismissButton = popup.querySelector("[data-notification-dismiss]");
    if (dismissButton) {
        dismissButton.addEventListener("click", hidePopup);
    }

    const viewLink = popup.querySelector("[data-notification-view]");
    if (viewLink) {
        viewLink.addEventListener("click", rememberNotification);
    }
});
