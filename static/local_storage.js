(() => {
    const STORAGE_KEY = "calculateur-moyennes:data:v1";
    const stateElement = document.getElementById("server-state");

    if (!stateElement) {
        return;
    }

    function readLocalState() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            return raw === null ? null : JSON.parse(raw);
        } catch (error) {
            console.warn("Impossible de lire le stockage local.", error);
            return null;
        }
    }

    function writeLocalState(state) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
            return true;
        } catch (error) {
            console.warn("Impossible d'écrire dans localStorage.", error);
            return false;
        }
    }

    // L'ordre des clés JSON n'a pas de signification fonctionnelle.
    function normaliserPourComparaison(value) {
        if (Array.isArray(value)) {
            return value.map(normaliserPourComparaison);
        }
        if (value !== null && typeof value === "object") {
            return Object.keys(value).sort().reduce((result, key) => {
                result[key] = normaliserPourComparaison(value[key]);
                return result;
            }, {});
        }
        return value;
    }

    function sameState(first, second) {
        return JSON.stringify(normaliserPourComparaison(first))
            === JSON.stringify(normaliserPourComparaison(second));
    }

    function cleanSyncParameter(url) {
        url.searchParams.delete("sync");
        return url.toString();
    }

    async function envoyerEtatAuServeur(state) {
        const response = await fetch("/api/synchroniser", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')?.content || "",
            },
            body: JSON.stringify(state),
        });

        if (!response.ok) {
            throw new Error("La synchronisation a échoué (" + response.status + ").");
        }

        return response.json();
    }

    async function initialiserStockageLocal() {
        let serverState;
        try {
            serverState = JSON.parse(stateElement.textContent);
        } catch (error) {
            console.warn("État serveur invalide.", error);
            return;
        }

        const localState = readLocalState();
        const alreadyInitialized = stateElement.dataset.initialized === "true";

        if (!alreadyInitialized) {
            // Migration unique : on importe l'ancien état du navigateur. Si
            // aucune copie locale n'existe, on initialise le profil avec l'état serveur.
            try {
                const savedState = await envoyerEtatAuServeur(localState ?? serverState);
                writeLocalState(savedState);
                window.location.reload();
            } catch (error) {
                // Ne jamais effacer la copie locale si l'import échoue.
                console.warn("Import initial impossible ; les données locales sont conservées.", error);
            }
            return;
        }

        // Après l'import initial, PostgreSQL est la source de vérité.
        if (localState === null || !sameState(localState, serverState)) {
            writeLocalState(serverState);
        }
    }

    async function recupererEtatApresModification() {
        const response = await fetch("/api/etat", { cache: "no-store" });
        if (!response.ok) {
            throw new Error("Impossible de récupérer l'état du serveur.");
        }
        return response.json();
    }

    document.addEventListener("submit", async (event) => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement) || form.method.toLowerCase() !== "post") {
            return;
        }
        if (form.dataset.nativeSubmit === "true" || form.dataset.submitting === "true") {
            return;
        }

        event.preventDefault();
        form.dataset.submitting = "true";

        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
        }

        let response;
        try {
            response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
            });
        } catch (error) {
            console.warn("La soumission JavaScript a échoué.", error);
            form.dataset.submitting = "false";
            if (submitButton) {
                submitButton.disabled = false;
            }
            form.dataset.nativeSubmit = "true";
            form.submit();
            return;
        }

        if (response.redirected) {
            const redirectUrl = new URL(response.url);
            if (redirectUrl.searchParams.get("sync") !== "0") {
                try {
                    const state = await recupererEtatApresModification();
                    // En cas d'échec d'écriture, on garde l'ancienne copie :
                    // la supprimer empêcherait toute récupération locale.
                    writeLocalState(state);
                } catch (error) {
                    console.warn("Impossible de mettre à jour le stockage local ; aucune donnée locale n'est supprimée.", error);
                }
            }
            window.location.assign(cleanSyncParameter(redirectUrl));
            return;
        }

        const html = await response.text();
        document.open();
        document.write(html);
        document.close();
    });

    initialiserStockageLocal();
})();
