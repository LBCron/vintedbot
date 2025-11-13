const API_URL = 'https://vintedbot-backend.fly.dev';

document.getElementById('captureBtn').addEventListener('click', async () => {
    const btn = document.getElementById('captureBtn');
    const successMsg = document.getElementById('successMsg');
    const errorMsg = document.getElementById('errorMsg');
    const statusMsg = document.getElementById('statusMsg');
    const accountName = document.getElementById('accountName').value;

    // Reset messages
    successMsg.style.display = 'none';
    errorMsg.style.display = 'none';
    statusMsg.textContent = '';

    // Disable button
    btn.disabled = true;
    btn.textContent = 'Capture en cours...';

    try {
        // Vérifier si on est sur vinted.fr
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tab.url || (!tab.url.includes('vinted.fr') && !tab.url.includes('vinted.com'))) {
            throw new Error('Ouvre d\'abord vinted.fr dans un onglet');
        }

        statusMsg.textContent = 'Récupération des cookies...';

        // Récupérer tous les cookies de vinted.fr
        const cookies = await chrome.cookies.getAll({
            domain: '.vinted.fr'
        });

        if (cookies.length === 0) {
            throw new Error('Aucun cookie trouvé. Connecte-toi d\'abord sur vinted.fr');
        }

        statusMsg.textContent = `${cookies.length} cookies trouvés`;

        // Formater les cookies en string
        const cookieString = cookies
            .map(cookie => `${cookie.name}=${cookie.value}`)
            .join('; ');

        // Récupérer le user agent
        const userAgent = navigator.userAgent;

        statusMsg.textContent = 'Envoi au backend...';

        // Récupérer le token d'authentification depuis le localStorage de VintedBot
        // On ne peut pas accéder directement au localStorage d'un autre domaine
        // donc l'utilisateur devra être connecté sur VintedBot

        // Pour l'instant, on va juste copier le cookie dans le presse-papier
        // et afficher un message pour que l'utilisateur le colle manuellement

        // Essayer d'envoyer au backend si possible
        try {
            // Demander à l'utilisateur son token VintedBot
            const token = prompt('Entre ton token VintedBot (ou laisse vide pour copier le cookie):');

            if (token) {
                const response = await fetch(`${API_URL}/accounts/add`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        name: accountName,
                        cookie: cookieString,
                        user_agent: userAgent
                    })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Erreur lors de l\'ajout du compte');
                }

                successMsg.innerHTML = `✅ Compte "${accountName}" ajouté avec succès!`;
                successMsg.style.display = 'block';
            } else {
                // Copier dans le presse-papier
                await navigator.clipboard.writeText(cookieString);
                successMsg.innerHTML = `✅ Cookie copié! Colle-le sur vintedbot-frontend.fly.dev/accounts`;
                successMsg.style.display = 'block';
            }
        } catch (e) {
            // Si l'envoi échoue, copier dans le presse-papier
            await navigator.clipboard.writeText(cookieString);
            successMsg.innerHTML = `✅ Cookie copié dans le presse-papier!<br>Colle-le sur <a href="https://vintedbot-frontend.fly.dev/accounts" target="_blank">VintedBot</a>`;
            successMsg.style.display = 'block';
        }

        statusMsg.textContent = '';

    } catch (error) {
        errorMsg.textContent = `❌ ${error.message}`;
        errorMsg.style.display = 'block';
        statusMsg.textContent = '';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Capturer Cookie Vinted';
    }
});
