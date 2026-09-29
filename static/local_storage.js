(() => {
    const STORAGE_KEY = "calculateur-moyennes:data:v1";
    const stateElement = document.getElementById("server-state");

    if (!stateElement) {
        return;
    }

    function readLocalState() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);

            if (raw === null) {
                return null;
            }

            return JSON.parse(raw);
        } catch (error) {
            console.warn("Impossible de lire le stockage local.", error);
            return null;
        }
    }

    function writeLocalState(state) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }

    function sameState(first, second) {
        return JSON.stringify(first) === JSON.stringify(second);
    }

    function cleanSyncParameter(url) {
        url.searchParams.delete("sync");
        return url.toString();
    }

    async function synchroniserAvecLeServeur(localState) {
        const response = await fetch("/api/synchroniser", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(localState),
        });

        if (!response.ok) {
            throw new Error("La synchronisation a échoué.");
        }

        window.location.reload();
    }

    async function initialiserStockageLocal() {
        let serverState;

        try {
            serverState = JSON.parse(stateElement.textContent);
        } catch (error) {
            console.warn("État serveur invalide.", error);
            return;
        }

        let localState = readLocalState();

        if (localState === null) {
            try {
                writeLocalState(serverState);
            } catch (error) {
                console.warn("Impossible d'écrire dans localStorage.", error);
            }
            return;
        }

        if (!sameState(localState, serverState)) {
            try {
                await synchroniserAvecLeServeur(localState);
            } catch (error) {
                console.warn("Impossible de synchroniser les données.", error);
            }
        }
    }

    async function recupererEtatApresModification() {
        const response = await fetch("/api/etat", {
            cache: "no-store",
        });

        if (!response.ok) {
            throw new Error("Impossible de récupérer l'état du serveur.");
        }

        return response.json();
    }

    document.addEventListener("submit", async (event) => {
        const form = event.target;

        if (!(form instanceof HTMLFormElement)) {
            return;
        }

        if (form.method.toLowerCase() !== "post") {
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

        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
            });

            if (response.redirected) {
                const redirectUrl = new URL(response.url);

                if (redirectUrl.searchParams.get("sync") !== "0") {
                    const state = await recupererEtatApresModification();
                    writeLocalState(state);
                }

                window.location.assign(cleanSyncParameter(redirectUrl));
                return;
            }

            const html = await response.text();
            document.open();
            document.write(html);
            document.close();
        } catch (error) {
            console.warn("La soumission JavaScript a échoué.", error);
            form.dataset.submitting = "false";
            if (submitButton) {
                submitButton.disabled = false;
            }
            form.dataset.nativeSubmit = "true";
            form.submit();
        }
    });

    initialiserStockageLocal();
})();
