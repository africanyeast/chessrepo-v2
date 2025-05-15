import LichessPgnViewer from '/static/viewer/viewer.js';

// Global variables
let pgnViewerInstance = null;
let gamePgnPositionParent = null;
let pgnCache = {};

function initializeOrUpdateViewer(element, pgn) {
    // Store the parent element reference on first call
    if (!gamePgnPositionParent && element) {
        gamePgnPositionParent = element.parentElement;
    }
    
    // If the original element is no longer in the DOM, recreate it
    if (!element || !document.body.contains(element)) {
        if (!gamePgnPositionParent || !document.body.contains(gamePgnPositionParent)) {
            return;
        }
        
        // Clear the parent and create a new container
        gamePgnPositionParent.innerHTML = '';
        const newElement = document.createElement('div');
        newElement.id = 'gamePgnPosition';
        gamePgnPositionParent.appendChild(newElement);
        element = newElement;
    }

    // Clear previous instance if any
    if (pgnViewerInstance && pgnViewerInstance.destroy) {
        try {
            pgnViewerInstance.destroy();
        } catch (e) {
            // Silent error handling
        }
        pgnViewerInstance = null;
    }
    
    const noPgnText = "PGN not available for this game.";

    if (pgn) {
        try {
            pgnViewerInstance = LichessPgnViewer(element, {
                pgn: pgn,
                showMoves: 'auto',
                keyboardToMove: true,
                initialPly: 0,
                showPlayers: true,
                showClocks: true,
                showControls: true,
                orientation: undefined,
            });
        } catch (e) {
            element.innerHTML = `<p class="text-center p-3 text-muted">Error loading PGN viewer.</p>`;
        }
    } else {
        element.innerHTML = `<p class="text-center p-3 text-muted">${noPgnText}</p>`;
    }
}

// Function to fetch PGN data for a game
async function fetchGamePGN(gameId) {
    // Check if we already have this PGN in cache
    if (pgnCache[gameId]) {
        return pgnCache[gameId];
    }
    
    try {
        const response = await fetch(`/api/game/${gameId}/pgn/`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        
        if (data.success) {
            // Store in cache for future use
            pgnCache[gameId] = data;
            return data;
        } else {
            throw new Error(data.error || 'Failed to fetch PGN data');
        }
    } catch (error) {
        return null;
    }
}

document.addEventListener('DOMContentLoaded', function () {
    // DOM elements
    const gamesSectionWrapper = document.getElementById('gamesSectionWrapper');
    const gameDisplayWrapper = document.getElementById('gameDisplayWrapper');
    //const gameViewSection = document.getElementById('gameViewDisplay');
    const gameLoader = document.getElementById('gameLoader');
    
    // Game detail elements
    let gamePlayerNames = document.getElementById('gamePlayerNames');
    let gameTournamentName = document.getElementById('gameTournamentName');
    let gameResult = document.getElementById('gameResult');
    let gameOpening = document.getElementById('gameOpening');
    let gameSite = document.getElementById('gameSite');
    let gameFormat = document.getElementById('gameFormat');
    
    // Game view containers
    let gameViewHeader = document.querySelector('.game-view-header');
    let gameViewInfo = document.querySelector('.game-view-info');
    let chessBoardContainer = document.querySelector('.chess-board-container');
    
    let currentSelectedGameRow = null;

    // Function to set initial state (no game selected)
    function setInitialLayout() {
        gameDisplayWrapper.classList.add('d-none');
        gameDisplayWrapper.classList.remove('col-md-6', 'col-lg-6');
        gamesSectionWrapper.classList.remove('col-md-6', 'col-lg-6');
        gamesSectionWrapper.classList.add('col-12', 'col-md-8', 'col-lg-5', 'mx-auto');
    }

    // Function to set active game layout
    function setActiveGameLayout() {
        gameDisplayWrapper.classList.remove('d-none');
        gameDisplayWrapper.classList.add('col-md-6', 'col-lg-7'); 
        gamesSectionWrapper.classList.remove('col-12', 'col-md-8', 'col-lg-5', 'mx-auto');
        gamesSectionWrapper.classList.add('col-md-6', 'col-lg-5');
    }

    // Function to show loading state
    function showLoading() {
        if (gameViewHeader) gameViewHeader.style.display = 'none';
        if (gameViewInfo) gameViewInfo.style.display = 'none';
        if (chessBoardContainer) chessBoardContainer.style.display = 'none';
        
        // Make sure to set display to 'flex' or 'block' instead of just removing 'none'
        if (gameLoader) {
            gameLoader.style.display = 'flex';
            // Force a reflow to ensure the loader is visible
            gameLoader.offsetHeight;
        }
    }

    // Function to show game details
    function showGameDetails() {
        // Explicitly hide the loader
        if (gameLoader) gameLoader.style.display = 'none';
        
        if (gameViewHeader) gameViewHeader.style.display = '';
        if (gameViewInfo) gameViewInfo.style.display = '';
        if (chessBoardContainer) chessBoardContainer.style.display = '';
    }

    // Function to create a title badge element
    function createTitleBadge(title) {
        if (!title) return null;
        
        // Normalize the title (uppercase and trim)
        const normalizedTitle = title.toUpperCase().trim();
        
        // Create the badge element
        const badge = document.createElement('span');
        badge.className = `chess-title-badge`;
        badge.textContent = normalizedTitle;
        
        return badge;
    }

    // Function to format player name with title
    function formatPlayerWithTitle(name, title, username, elo) {
        const container = document.createElement('span');
        container.className = 'player-name-container';
        
        // Add title badge if player has a title
        if (title) {
            const badge = createTitleBadge(title);
            if (badge) {
                container.appendChild(badge);
            }
        }
        
        // Add player name
        const nameSpan = document.createElement('span');
        nameSpan.className = 'player-name';
        //nameSpan.textContent = name || username || 'N/A';
        // add not just name but also elo in brackets
        nameSpan.innerHTML = `${name || username || 'N/A'} <span class="player-elo">(${elo || '-'})</span>`;
        container.appendChild(nameSpan);
        
        return container;
    }

    // Function to handle game selection
    async function handleGameSelection(gameRow) {
        if (!gameRow) return;
        
        // Update selected game styling
        if (currentSelectedGameRow) {
            currentSelectedGameRow.classList.remove('selected-game');
        }
        gameRow.classList.add('selected-game');
        currentSelectedGameRow = gameRow;
    
        // Set layout for active game
        setActiveGameLayout();
        
        // Show loading state
        showLoading();
        
        // Get game ID from data attribute
        const gameId = gameRow.dataset.gameId;
        
        // Fetch game data
        const gameData = await fetchGamePGN(gameId);
        
        if (gameData && gameData.pgn) {
            // Clear the player names container
            gamePlayerNames.innerHTML = '';
            
            // Create white player element with title
            const whitePlayerElement = formatPlayerWithTitle(
                gameData.white_name,
                gameData.white_title,
                gameData.white_username,
                gameData.whiteelo
            );
            
            // Create separator with proper spacing
            const separator = document.createElement('span');
            separator.className = 'player-name-separator';
            separator.textContent = '-';
            
            // Create black player element with title
            const blackPlayerElement = formatPlayerWithTitle(
                gameData.black_name,
                gameData.black_title,
                gameData.black_username,
                gameData.blackelo
            );
            
            // Add white player, separator, and black player
            gamePlayerNames.appendChild(whitePlayerElement);
            gamePlayerNames.appendChild(separator);
            gamePlayerNames.appendChild(blackPlayerElement);
            
            // Update other game information
            gameTournamentName.textContent = gameData.tournament || 'N/A';
            gameResult.textContent = formatGameResult(gameData.result);
            gameOpening.textContent = gameData.opening || '-';
            gameSite.textContent = (gameData.site && gameData.site.trim() !== '?') ? gameData.site : '-';
            gameFormat.textContent = gameData.format || '-';
            
            // Initialize PGN viewer
            const gamePgnPosition = document.getElementById('gamePgnPosition');
            initializeOrUpdateViewer(gamePgnPosition, gameData.pgn);
            
            // Show game details
            showGameDetails();
        } else {
            // Handle error case
            const gamePgnPosition = document.getElementById('gamePgnPosition');
            if (gamePgnPosition) {
                gamePgnPosition.innerHTML = '<p class="text-center p-3 text-muted">Failed to load game data.</p>';
            }
            showGameDetails();
        }
    }

    // Initialize game rows
    const gameRows = document.querySelectorAll('.game-row-interactive');
    gameRows.forEach(row => {
        row.addEventListener('click', function() {
            handleGameSelection(this);
        });
    });

    // Initialize the page
    setInitialLayout();
    
    // Initialize tournament containers based on game count
    initializeTournamentContainers();

    // set theme and store choice in browser storage
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = themeToggle.querySelector('i');
    const currentTheme = localStorage.getItem('theme') || 'light';

    // Initial setup based on stored preference
    if (currentTheme === 'dark') {
        document.body.classList.add('dark-mode');
        themeIcon.className = 'bi bi-sun-fill text-white';
    } else {
        themeIcon.className = 'bi bi-moon-stars-fill text-white';
    }

    // Toggle theme when button is clicked
    themeToggle.addEventListener('click', function () {
        document.body.classList.toggle('dark-mode');
        const isDarkMode = document.body.classList.contains('dark-mode');
        const newTheme = isDarkMode ? 'dark' : 'light';
        
        // Update icon and text based on new theme
        if (isDarkMode) {
            themeIcon.className = 'bi bi-sun-fill text-white';
        } else {
            themeIcon.className = 'bi bi-moon-stars-fill text-white';
        }
        
        localStorage.setItem('theme', newTheme);
    });
});


/**
 * Toggle tournament games visibility
 * @param {HTMLElement} headerElement - The tournament header element
 */
function toggleTournament(headerElement) {
    const container = headerElement.closest('.tournament-container');
    const gamesContainer = container.querySelector('.games-container');
    const toggleIcon = headerElement.querySelector('.toggle-icon i');
    
    if (gamesContainer.style.display === 'none') {
        gamesContainer.style.display = 'block';
        toggleIcon.classList.remove('bi-chevron-down');
        toggleIcon.classList.add('bi-chevron-up');
    } else {
        gamesContainer.style.display = 'none';
        toggleIcon.classList.remove('bi-chevron-up');
        toggleIcon.classList.add('bi-chevron-down');
    }
}

/**
 * Toggle player group games visibility
 * @param {HTMLElement} headerElement - The player group header element
 */
function togglePlayerGroup(headerElement) {
    const container = headerElement.closest('.player-group-container');
    const gamesContainer = container.querySelector('.player-games-container');
    const toggleIcon = headerElement.querySelector('.toggle-icon i');
    
    if (gamesContainer.style.display === 'none') {
        gamesContainer.style.display = 'block';
        toggleIcon.classList.remove('bi-chevron-down');
        toggleIcon.classList.add('bi-chevron-up');
    } else {
        gamesContainer.style.display = 'none';
        toggleIcon.classList.remove('bi-chevron-up');
        toggleIcon.classList.add('bi-chevron-down');
    }
}

/**
 * Initialize tournament containers based on game count
 * Sets initial state: open if ≤10 games, closed if >10 games
 */
function initializeTournamentContainers() {
    document.querySelectorAll('.tournament-container').forEach(container => {
        // Count individual games and player groups
        const individualGames = container.querySelectorAll('.games-container > .game-row-interactive:not(.player-group-container .game-row-interactive)').length;
        const playerGroups = container.querySelectorAll('.games-container > .player-group-container').length;
        
        // Total count (individual games + player groups)
        const totalItems = individualGames + playerGroups;
        
        // Get elements
        const gamesContainer = container.querySelector('.games-container');
        const toggleIcon = container.querySelector('.event-header .toggle-icon i');
        
        if (totalItems > 10) {
            // If more than 10 items, close by default
            gamesContainer.style.display = 'none';
            toggleIcon.classList.remove('bi-chevron-up');
            toggleIcon.classList.add('bi-chevron-down');
        } else {
            // If 10 or fewer items, open by default
            gamesContainer.style.display = 'block';
            toggleIcon.classList.remove('bi-chevron-down');
            toggleIcon.classList.add('bi-chevron-up');
        }
    });
}

function formatGameResult(result) {
    if (result === "1/2-1/2") {
        return "½-½";
    }
    return result;
}

// Make functions available globally
window.togglePlayerGroup = togglePlayerGroup;
window.toggleTournament = toggleTournament;