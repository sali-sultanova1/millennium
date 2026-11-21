const FAVORITES_KEY = "millennium_favorites";
const checkboxSelector = 'input[type="checkbox"][name="ids"]';

function readFavorites() {
    try {
        const stored = JSON.parse(localStorage.getItem(FAVORITES_KEY) || "[]");
        if (!Array.isArray(stored)) return [];
        return [...new Set(stored.map(String).filter((id) => /^[1-9]\d{0,18}$/.test(id)))];
    } catch {
        return [];
    }
}

function saveFavorites(ids) {
    try {
        localStorage.setItem(FAVORITES_KEY, JSON.stringify(ids));
        return true;
    } catch {
        const feedback = document.querySelector("#favorite-feedback");
        feedback.classList.add("visible-feedback");
        feedback.textContent = "Браузер не смог сохранить избранное на этом устройстве.";
        return false;
    }
}

function updateFavoriteButton(button, isFavorite) {
    const label = button.querySelector("[data-favorite-label]");
    if (label) label.textContent = isFavorite ? "В избранном" : "В избранное";
    if (button.classList.contains("heart-btn")) button.title = isFavorite ? "Убрать из избранного" : "В избранное";
    button.setAttribute("aria-pressed", String(isFavorite));
}

const favoriteButtons = document.querySelectorAll("[data-favorite-id]");

function syncFavoriteButtons() {
    const ids = readFavorites();
    for (const button of favoriteButtons) {
        updateFavoriteButton(button, ids.includes(button.dataset.favoriteId));
    }
}

syncFavoriteButtons();
for (const button of favoriteButtons) {
    button.addEventListener("click", () => {
        const tourId = button.dataset.favoriteId;
        const ids = readFavorites();
        const wasFavorite = ids.includes(tourId);
        const updated = wasFavorite ? ids.filter((id) => id !== tourId) : [...ids, tourId];
        if (saveFavorites(updated)) syncFavoriteButtons();
    });
}
window.addEventListener("pageshow", syncFavoriteButtons);
window.addEventListener("storage", (event) => {
    if (event.key === FAVORITES_KEY || event.key === null) syncFavoriteButtons();
});

async function loadFavoriteItems(list, ids, signal) {
    const url = new URL(list.dataset.itemsUrl, window.location.href);
    for (const id of ids) url.searchParams.append("ids", id);
    if (list.dataset.pickerMode) url.searchParams.set("mode", list.dataset.pickerMode);
    list.setAttribute("aria-busy", "true");
    try {
        const response = await fetch(url, {signal});
        if (!response.ok) throw new Error("Favorites request failed");
        list.innerHTML = await response.text();
        return true;
    } catch {
        if (signal?.aborted) return false;
        list.textContent = "Не удалось загрузить избранное. ";
        return false;
    } finally {
        if (!signal?.aborted) list.removeAttribute("aria-busy");
    }
}

function addRetry(list, reload) {
    const retry = document.createElement("button");
    retry.type = "button";
    retry.className = "btn secondary";
    retry.textContent = "Попробовать снова";
    retry.addEventListener("click", reload, {once: true});
    list.append(retry);
}

function setAllChecked(list, checked) {
    for (const box of list.querySelectorAll(checkboxSelector)) box.checked = checked;
}

function initFavoritesPage(form) {
    const list = form.querySelector("#favorites-list");
    const tools = form.querySelector("#favorites-tools");
    const footer = form.querySelector("#favorites-submit");
    const message = form.querySelector("#favorites-selection-error");
    const count = form.querySelector("#favorites-count");
    let currentRequest;

    function showCount() {
        const checked = list.querySelectorAll(checkboxSelector + ":checked").length;
        count.textContent = "Выбрано " + checked + " из " + list.querySelectorAll(checkboxSelector).length;
        if (checked) message.textContent = "";
    }

    function showList() {
        const hasItems = Boolean(list.querySelector(checkboxSelector));
        tools.hidden = !hasItems;
        footer.hidden = !hasItems;
        if (!hasItems) {
            const template = form.querySelector("#favorites-empty");
            list.replaceChildren(template.content.cloneNode(true));
            message.textContent = "";
        }
        showCount();
    }

    async function reload() {
        currentRequest?.abort();
        currentRequest = new AbortController();
        const {signal} = currentRequest;
        const checkedIds = new Set([...list.querySelectorAll(checkboxSelector + ":checked")].map(box => box.value));
        const ids = readFavorites();
        if (!ids.length) {
            list.replaceChildren();
            list.removeAttribute("aria-busy");
        } else if (!await loadFavoriteItems(list, ids, signal)) {
            if (signal.aborted) return;
            tools.hidden = true;
            footer.hidden = true;
            addRetry(list, reload);
            return;
        }
        for (const box of list.querySelectorAll(checkboxSelector)) box.checked = checkedIds.has(box.value);
        showList();
    }

    list.addEventListener("change", showCount);
    list.addEventListener("click", (event) => {
        const button = event.target.closest("[data-remove-favorite-id]");
        if (!button) return;
        const ids = readFavorites().filter((id) => id !== button.dataset.removeFavoriteId);
        if (!saveFavorites(ids)) return;
        button.closest("[data-favorite-card]").remove();
        showList();
        const next = list.querySelector(checkboxSelector) || list.querySelector("a");
        if (next) next.focus();
    });
    form.querySelector("#select-all-favorites").addEventListener("click", () => {
        setAllChecked(list, true);
        showCount();
    });
    form.querySelector("#clear-favorites-selection").addEventListener("click", () => {
        setAllChecked(list, false);
        showCount();
    });
    form.addEventListener("submit", (event) => {
        if (!list.querySelector(checkboxSelector + ":checked")) {
            event.preventDefault();
            message.textContent = "Выберите хотя бы один тур.";
            list.querySelector(checkboxSelector)?.focus();
        }
    });
    window.addEventListener("pageshow", event => {
        if (event.persisted) reload();
    });
    window.addEventListener("storage", event => {
        if (event.key === FAVORITES_KEY || event.key === null) reload();
    });
    reload();
}

function initInquiryFavorites(section) {
    const list = section.querySelector("#inquiry-favorites-list");
    const restored = JSON.parse(document.querySelector("#inquiry-selected-tour-ids").textContent).map(String);
    const ids = [...new Set([...readFavorites(), ...restored])];
    if (!ids.length) return;

    async function reload() {
        if (!await loadFavoriteItems(list, ids)) {
            section.hidden = false;
            addRetry(list, reload);
            return;
        }
        
    document.querySelector("#restored-tour-inputs")?.remove();
        const boxes = list.querySelectorAll(checkboxSelector);
        for (const box of boxes) box.checked = restored.includes(box.value);
        section.hidden = !boxes.length;
        section.querySelector("#inquiry-favorites-actions").hidden = boxes.length < 2;
    }
    section.querySelector("#inquiry-select-all").addEventListener("click", () => setAllChecked(list, true));
    section.querySelector("#inquiry-clear-selection").addEventListener("click", () => setAllChecked(list, false));
    reload();
}

const selectionForm = document.querySelector("#favorites-selection");
if (selectionForm) initFavoritesPage(selectionForm);
const inquiryFavorites = document.querySelector("#inquiry-favorites");
if (inquiryFavorites) initInquiryFavorites(inquiryFavorites);
