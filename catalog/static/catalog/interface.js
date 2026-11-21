const menu = document.querySelector("#mobile-menu");

if (menu) {
    document.addEventListener("click", (event) => {
        if (menu.open && (!menu.contains(event.target) || event.target.closest("a"))) menu.open = false;
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && menu.open) {
            menu.open = false;
            menu.querySelector("summary").focus();
        }
    });
}

const catalogFilters = document.querySelector(".catalog-filters");
const sortControl = document.querySelector("#catalog-sort");
sortControl?.addEventListener("change", () => sortControl.form.requestSubmit());

if (catalogFilters) {
    const narrowScreen = window.matchMedia("(max-width: 46rem)");
    const adjustFilters = () => { catalogFilters.open = !narrowScreen.matches; };
    adjustFilters();
    narrowScreen.addEventListener("change", adjustFilters);
}

const gallery = document.querySelector("[data-gallery]");
if (gallery) {
    const dialog = gallery.querySelector("dialog");
    const photos = [...gallery.querySelectorAll("[data-gallery-photo]")];
    const image = dialog.querySelector("[data-full-photo]");
    const caption = dialog.querySelector("[data-caption]");
    const counter = dialog.querySelector("[data-photo-count]");
    let index = 0;

    function showPhoto(next) {
        index = (next + photos.length) % photos.length;
        image.src = photos[index].href;
        image.alt = photos[index].dataset.alt;
        caption.textContent = image.alt;
        counter.textContent = (index + 1) + " / " + photos.length;
    }

    photos.forEach((link, i) => {
        link.addEventListener("click", (event) => {
            if (typeof dialog.showModal !== "function" || event.metaKey || event.ctrlKey || event.altKey || event.shiftKey) return;
            event.preventDefault();
            showPhoto(i);
            dialog.showModal();
        });
    });
    dialog.querySelector("[data-next]")?.addEventListener("click", () => showPhoto(index + 1));
    dialog.querySelector("[data-previous]")?.addEventListener("click", () => showPhoto(index - 1));
    dialog.querySelector("[data-close]").addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
        if (event.target === dialog) dialog.close();
    });
    dialog.addEventListener("keydown", (event) => {
        if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
            event.preventDefault();
            showPhoto(index + (event.key === "ArrowRight" ? 1 : -1));
        }
    });
}

document.addEventListener("invalid", (event) => {
    const preferences = event.target.closest("details.preferences");
    if (preferences) preferences.open = true;
}, true);

function revealLinkedField() {
    const field = document.getElementById(location.hash.slice(1));
    const group = field?.closest("details.preferences");
    if (group) {
        group.open = true;
        field.focus();
    }
}
window.addEventListener("hashchange", revealLinkedField);
revealLinkedField();
