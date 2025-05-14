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
    function formatPlayerWithTitle(name, title, username) {
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
        nameSpan.textContent = name || username || 'N/A';
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
                gameData.white_username
            );
            
            // Create separator with proper spacing
            const separator = document.createElement('span');
            separator.className = 'player-name-separator';
            separator.textContent = '-';
            
            // Create black player element with title
            const blackPlayerElement = formatPlayerWithTitle(
                gameData.black_name,
                gameData.black_title,
                gameData.black_username
            );
            
            // Add white player, separator, and black player
            gamePlayerNames.appendChild(whitePlayerElement);
            gamePlayerNames.appendChild(separator);
            gamePlayerNames.appendChild(blackPlayerElement);
            
            // Update other game information
            gameTournamentName.textContent = gameData.tournament || 'N/A';
            gameResult.textContent = gameData.result || 'N/A';
            gameOpening.textContent = gameData.opening || '-';
            gameSite.textContent = gameData.site || '-';
            
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
 * Filter games based on format or variant
 * @param {string} filterValue - The format to filter by (bullet, blitz, rapid, classical) or 'all'
 * @param {boolean} isVariant - Whether to filter by variant instead of format (for Chess960)
 */
function filterGames(filterValue, isVariant = false) {
    // Update active class on filter buttons
    document.querySelectorAll('.filter-nav .nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.textContent.toLowerCase() === filterValue || 
            (filterValue === 'all' && link.textContent.toLowerCase() === 'all')) {
            link.classList.add('active');
        }
    });
    
    // Get all game elements
    const gameElements = document.querySelectorAll('.game-row-interactive');
    
    // Show/hide games based on filter
    let visibleGamesCount = 0;
    
    // First, make all tournament containers visible again
    document.querySelectorAll('.tournament-container').forEach(container => {
        container.style.display = '';
    });
    
    // Remove any existing "no games found" message
    const existingNoGamesMessage = document.querySelector('.no-filtered-games-message, .no-games-message');
    if (existingNoGamesMessage) {
        existingNoGamesMessage.remove();
    }
    
    // Special handling for "all" filter - show everything
    if (filterValue === 'all') {
        gameElements.forEach(gameEl => {
            gameEl.style.display = '';
            visibleGamesCount++;
        });
        
        // Show all player groups
        document.querySelectorAll('.player-group-container').forEach(group => {
            group.style.display = '';
        });
        
        // Restore original tournament counts
        document.querySelectorAll('.tournament-container').forEach(tournamentGroup => {
            const totalGames = parseInt(tournamentGroup.getAttribute('data-total-games'));
            const tournamentNameEl = tournamentGroup.querySelector('.tournament-name');
            if (tournamentNameEl) {
                const gameCountEl = tournamentNameEl.querySelector('.game-count');
                if (gameCountEl) {
                    gameCountEl.textContent = `(${totalGames})`;
                }
            }
        });
    } else {
        // Filter games by format or variant
        const visibleGameElements = [];
        const hiddenGameElements = [];
        
        gameElements.forEach(gameEl => {
            const gameFormat = gameEl.getAttribute('data-format');
            const gameVariant = gameEl.getAttribute('data-variant');
            
            const matchesFilter = isVariant 
                ? (gameVariant && gameVariant.toLowerCase() === filterValue.toLowerCase())
                : (gameFormat && gameFormat.toLowerCase() === filterValue.toLowerCase());
            
            if (matchesFilter) {
                gameEl.style.display = '';
                visibleGameElements.push(gameEl);
                visibleGamesCount++;
            } else {
                gameEl.style.display = 'none';
                hiddenGameElements.push(gameEl);
            }
        });
        
        // Process player groups - hide those with no visible games
        document.querySelectorAll('.player-group-container').forEach(group => {
            const groupGames = Array.from(group.querySelectorAll('.game-row-interactive'));
            const visibleGroupGames = groupGames.filter(game => 
                visibleGameElements.includes(game)
            );
            
            if (visibleGroupGames.length === 0) {
                // Hide the entire group if no games match the filter
                group.style.display = 'none';
            } else {
                group.style.display = '';
                
                // Update the game count in the player group header
                const playerGroupNameEl = group.querySelector('.player-group-name');
                if (playerGroupNameEl) {
                    const gameCountEl = playerGroupNameEl.querySelector('.game-count');
                    if (gameCountEl) {
                        gameCountEl.textContent = `(${visibleGroupGames.length})`;
                    }
                }
            }
        });
        
        // Process tournaments - hide those with no visible games
        document.querySelectorAll('.tournament-container').forEach(tournamentGroup => {
            // Check if this tournament has any visible games
            const tournamentGames = Array.from(tournamentGroup.querySelectorAll('.game-row-interactive'));
            const visibleTournamentGames = tournamentGames.filter(game => 
                visibleGameElements.includes(game)
            );
            
            if (visibleTournamentGames.length === 0) {
                // Hide the entire tournament if no games match the filter
                tournamentGroup.style.display = 'none';
            } else {
                // Update the tournament game count
                const tournamentNameEl = tournamentGroup.querySelector('.tournament-name');
                if (tournamentNameEl) {
                    const gameCountEl = tournamentNameEl.querySelector('.game-count');
                    if (gameCountEl) {
                        gameCountEl.textContent = `(${visibleTournamentGames.length})`;
                    }
                }
                
                // Update the tournament's data-filtered-games attribute
                tournamentGroup.setAttribute('data-filtered-games', visibleTournamentGames.length.toString());
            }
        });
    }
    // Check if there are any games at all
    if (visibleGamesCount === 0) {
        // Create new message for "No games found"
        const noGamesMessage = document.createElement('div');
        noGamesMessage.className = 'p-3 text-center no-games-message';
        noGamesMessage.innerHTML = '<p>No games found</p>';
        
        // Add the new message
        const eventsContainer = document.querySelector('.events-container');
        if (eventsContainer) {
            eventsContainer.appendChild(noGamesMessage);
        }
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

// Make functions available globally
window.togglePlayerGroup = togglePlayerGroup;
window.toggleTournament = toggleTournament;
window.filterGames = filterGames;
