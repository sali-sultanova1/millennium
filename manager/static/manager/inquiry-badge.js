const inquiriesLink = document.querySelector("[data-inquiry-status-url]");

if (inquiriesLink) {
    const dot = inquiriesLink.querySelector("[data-inquiry-dot]");
    const announcement = inquiriesLink.querySelector("[data-inquiry-announcement]");
    let checking = false;

    async function updateInquiryBadge() {
        if (document.hidden || checking) return;
        checking = true;

        try {
            const response = await fetch(inquiriesLink.dataset.inquiryStatusUrl, {
                cache: "no-store",
                redirect: "error",
            });
            if (!response.ok) return;

            const { has_new: hasNew } = await response.json();
            dot.hidden = !hasNew;
            const message = hasNew ? "Есть новые заявки" : "";
            if (announcement.textContent !== message) announcement.textContent = message;
        } catch {
            // Preserve the last badge state until the next successful check.
        } finally {
            checking = false;
        }
    }

    updateInquiryBadge();
    window.setInterval(updateInquiryBadge, 20000);
    document.addEventListener("visibilitychange", updateInquiryBadge);
}
