const tourSearch = document.querySelector("[data-tour-search]");

if (tourSearch && typeof AbortController === "function") {
    const results = document.querySelector("[data-tour-search-results]");
    const reset = tourSearch.querySelector("[data-tour-search-reset]");
    const searchError = document.querySelector("[data-tour-search-error]");
    const status = document.querySelector("[data-tour-search-status]");
    let timer;
    let activeRequest;

    async function refreshTourResults() {
        const url = new URL(tourSearch.action);
        for (const [name, value] of new FormData(tourSearch)) {
            if (value.trim()) url.searchParams.set(name, value.trim());
        }

        const controller = new AbortController();
        activeRequest = controller;
        results.setAttribute("aria-busy", "true");
        searchError.hidden = true;

        try {
            const response = await fetch(url, { signal: controller.signal, cache: "no-store" });
            if (controller.signal.aborted) return;
            if (response.redirected) {
                window.location.assign(response.url);
                return;
            }
            if (!response.ok) throw new Error();

            const html = new DOMParser().parseFromString(await response.text(), "text/html");
            if (controller.signal.aborted) return;
            const nextResults = html.querySelector("[data-tour-search-results]");
            if (!nextResults) throw new Error();

            results.replaceChildren(...nextResults.childNodes);
            reset.hidden = html.querySelector("[data-tour-search-reset]").hidden;
            status.textContent = `Найдено туров — ${nextResults.dataset.resultCount}`;
            history.replaceState(history.state, "", url);
        } catch {
            if (!controller.signal.aborted) searchError.hidden = false;
        } finally {
            if (activeRequest === controller) {
                results.removeAttribute("aria-busy");
                activeRequest = null;
            }
        }
    }

    function scheduleTourSearch(delay) {
        clearTimeout(timer);
        activeRequest?.abort();
        timer = setTimeout(refreshTourResults, delay);
    }

    tourSearch.elements.q.addEventListener("input", event => {
        if (!event.isComposing) scheduleTourSearch(300);
    });
    tourSearch.elements.destination.addEventListener("change", () => scheduleTourSearch(0));
    tourSearch.addEventListener("submit", event => {
        event.preventDefault();
        scheduleTourSearch(0);
    });
}
