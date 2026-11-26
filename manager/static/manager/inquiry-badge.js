const inquiriesLink = document.querySelector("[data-inquiry-status-url]");

if (inquiriesLink) {
    const dot = inquiriesLink.querySelector("[data-inquiry-dot]");
    const count = inquiriesLink.querySelector("[data-inquiry-count]");
    const announcement = document.querySelector("[data-inquiry-announcement]");
    const notice = document.querySelector("[data-inquiry-notice]");
    const noticeText = notice.querySelector("[data-inquiry-notice-text]");
    let previousIds = new Set(JSON.parse(document.getElementById("new-inquiry-ids").textContent));
    let noticeIds = [];
    let checking = false;

    function updateIndicator(ids) {
        const hasNew = ids.size > 0;
        dot.hidden = !hasNew;
        const message = hasNew ? `Новые заявки (${ids.size})` : "";
        if (count.textContent !== message) count.textContent = message;
    }

    async function updateInquiryBadge() {
        if (checking) return;
        checking = true;

        try {
            const response = await fetch(inquiriesLink.dataset.inquiryStatusUrl, {
                cache: "no-store",
                redirect: "error",
            });
            if (!response.ok) return;

            const { new_ids: ids } = await response.json();
            if (!Array.isArray(ids)) return;
            const currentIds = new Set(ids);
            const arrivals = ids.filter(id => !previousIds.has(id));
            noticeIds = [...noticeIds.filter(id => currentIds.has(id)), ...arrivals];
            previousIds = currentIds;

            updateIndicator(currentIds);
            noticeText.textContent = noticeIds.length === 1 ? "Новая заявка" : "Поступили новые заявки";
            notice.hidden = noticeIds.length === 0;
            if (arrivals.length) {
                const latestId = arrivals[arrivals.length - 1];
                announcement.textContent = arrivals.length === 1
                    ? `Поступила новая заявка №${latestId}`
                    : `Поступили новые заявки. Последняя — №${latestId}`;
            }
        } catch {
            return;
        } finally {
            checking = false;
        }
    }

    notice.querySelector("[data-inquiry-dismiss]").addEventListener("click", () => {
        noticeIds = [];
        notice.hidden = true;
        inquiriesLink.focus();
    });
    updateIndicator(previousIds);
    window.setInterval(updateInquiryBadge, 20000);
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) updateInquiryBadge();
    });
    window.addEventListener("pageshow", event => {
        if (event.persisted) updateInquiryBadge();
    });
}
