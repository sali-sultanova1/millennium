const FAVORITES_KEY = "millennium_favorites";

function readFavorites() {
    const saved = localStorage.getItem(FAVORITES_KEY);

    if (saved === null) {
        return [];
    }

    try {
        const ids = JSON.parse(saved);
        if (Array.isArray(ids)) {
            return ids;
        } else {
            return [];
        }
    } catch {
        return [];
    }
}

function saveFavorites(ids) {
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(ids));
}

function updateFavoriteButton(button, isFavorite) {
    if (isFavorite) {
        button.textContent = "В избранном";
    } else {
        button.textContent = "В избранное";
    }

    button.setAttribute("aria-pressed", String(isFavorite));
}

const favoriteButtons = document.querySelectorAll("[data-favorite-id]");


for (const button of favoriteButtons) {
    const tourId = button.dataset.favoriteId;

    const ids = readFavorites();
    const isFavorite = ids.includes(tourId);
    updateFavoriteButton(button, isFavorite);

    button.addEventListener("click", () => {
        const ids = readFavorites();
        const wasFavorite = ids.includes(tourId);

        if (wasFavorite) {
            const remainingIds = ids.filter((id) => id !== tourId);
            saveFavorites(remainingIds);
        } else {
            ids.push(tourId);
            saveFavorites(ids);
        }

        updateFavoriteButton(button, !wasFavorite);
    });
}

async function loadFavoriteItems(list, ids = readFavorites()) {
    const params = new URLSearchParams();

    for (const id of ids) {
        params.append("ids", id);
    }

    if (list.dataset.pickerMode === "selection") {
        params.set("mode", "selection");
    }

    try {
        const response = await fetch(`${list.dataset.itemsUrl}?${params}`);

        if (!response.ok) {
            list.textContent = "Не удалось загрузить избранное.";
            return;
        }

        list.innerHTML = await response.text();
    } catch {
        list.textContent = "Не удалось загрузить избранное.";
    }
}

const favoritesList = document.querySelector("#favorites-list");

if (favoritesList) {
    loadFavoriteItems(favoritesList);

    favoritesList.addEventListener("click", (event) => {
        const button = event.target.closest("[data-remove-favorite-id]");

        if (!button) {
            return;
        }

        const tourId = button.dataset.removeFavoriteId;
        const remainingIds = readFavorites().filter((id) => id !== tourId);
        saveFavorites(remainingIds);

        button.closest("[data-favorite-card]").remove();

        if (!favoritesList.querySelector("[data-favorite-card]")) {
            favoritesList.textContent = "В избранном пока нет доступных туров.";
        }
    });
}

const selectionForm = document.querySelector("#favorites-selection");

if (selectionForm) {
    const checkboxSelector = 'input[type="checkbox"][name="ids"]';

    function setAllChecked(checked) {
        for (const checkbox of selectionForm.querySelectorAll(checkboxSelector)) {
            checkbox.checked = checked;
        }
    }

    document.querySelector("#select-all-favorites").addEventListener("click", () => {
        setAllChecked(true);
    });

    document.querySelector("#clear-favorites-selection").addEventListener("click", () => {
        setAllChecked(false);
    });

    selectionForm.addEventListener("submit", (event) => {
        const message = document.querySelector("#favorites-selection-error");

        if (!selectionForm.querySelector(`${checkboxSelector}:checked`)) {
            event.preventDefault();
            message.textContent = "Выберите хотя бы один тур.";
        } else {
            message.textContent = "";
        }
    });
}


async function initInquiryFavorites() {
    const section = document.querySelector("#inquiry-favorites");

    if (!section) {
        return;
    }

    const list = section.querySelector("#inquiry-favorites-list");
    const selectedData = document.querySelector("#inquiry-selected-tour-ids");
    const selectedIds = new Set(JSON.parse(selectedData.textContent).map(String));
    const idsToLoad = [...new Set([...readFavorites(), ...selectedIds])];

    if (idsToLoad.length === 0) {
        return;
    }

    await loadFavoriteItems(list, idsToLoad);

    const checkboxes = list.querySelectorAll('input[type="checkbox"][name="ids"]');

    if (checkboxes.length === 0) {
        return;
    }

    for (const checkbox of checkboxes) {
        checkbox.checked = selectedIds.has(checkbox.value);
    }

    section.hidden = false;

    if (checkboxes.length > 1) {
        section.querySelector("#inquiry-favorites-actions").hidden = false;

        section.querySelector("#inquiry-select-all").addEventListener("click", () => {
            for (const checkbox of checkboxes) {
                checkbox.checked = true;
            }
        });

        section.querySelector("#inquiry-clear-selection").addEventListener("click", () => {
            for (const checkbox of checkboxes) {
                checkbox.checked = false;
            }
        });
    }
}

initInquiryFavorites();