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
