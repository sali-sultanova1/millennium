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