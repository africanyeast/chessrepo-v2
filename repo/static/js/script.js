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
            // Update game details with data from API
            // Format player names based on the new data structure
            const whiteName = gameData.white ? 
                (gameData.white.name || gameData.white_username || 'N/A') : 
                (gameData.white_username || 'N/A');
            const blackName = gameData.black ? 
                (gameData.black.name || gameData.black_username || 'N/A') : 
                (gameData.black_username || 'N/A');
            
            gamePlayerNames.textContent = `${whiteName} - ${blackName}`;
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

    // set theme and store choice in browser storage
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = themeToggle.querySelector('i');
    const themeText = themeToggle.querySelector('small');
    const currentTheme = localStorage.getItem('theme') || 'light';

    // Initial setup based on stored preference
    if (currentTheme === 'dark') {
        document.body.classList.add('dark-mode');
        themeIcon.className = 'bi bi-sun-fill text-white';
        themeText.textContent = 'Light';
    } else {
        themeIcon.className = 'bi bi-moon-stars-fill text-white';
        themeText.textContent = 'Dark';
    }

    // Toggle theme when button is clicked
    themeToggle.addEventListener('click', function () {
        document.body.classList.toggle('dark-mode');
        const isDarkMode = document.body.classList.contains('dark-mode');
        const newTheme = isDarkMode ? 'dark' : 'light';
        
        // Update icon and text based on new theme
        if (isDarkMode) {
            themeIcon.className = 'bi bi-sun-fill text-white';
            themeText.textContent = 'Light';
        } else {
            themeIcon.className = 'bi bi-moon-stars-fill text-white';
            themeText.textContent = 'Dark';
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
 * Show more games for a tournament
 * @param {HTMLElement} button - The "Show More" button
 * @param {Array} [gamesToShow] - Optional array of game elements to show
 * @param {boolean} [resetButton] - Whether to reset the button state
 */
function showMoreGames(button, gamesToShow, resetButton = false) {
    const container = button.closest('.tournament-container');
    const hiddenGames = container.querySelector('.hidden-games');
    const gamesContainer = container.querySelector('.games-container');
    
    // Reset button if needed
    if (resetButton) {
        button.setAttribute('data-offset', '10');
    }
    
    const offset = parseInt(button.getAttribute('data-offset'));
    
    // If specific games are provided, use those
    if (gamesToShow && Array.isArray(gamesToShow)) {
        // Show up to 10 more games from the provided array
        const nextBatch = gamesToShow.slice(offset - 10, offset);
        let count = 0;
        
        nextBatch.forEach(game => {
            gamesContainer.insertBefore(game, button.parentElement);
            count++;
        });
        
        // Update the offset
        const newOffset = offset + count;
        button.setAttribute('data-offset', newOffset);
        
        // Hide the "Show More" button if all games are displayed
        const remainingGames = gamesToShow.length - (newOffset - 10);
        if (remainingGames <= 0) {
            button.parentElement.style.display = 'none';
        } else {
            button.parentElement.style.display = '';
        }
        
        return;
    }
    
    // Original functionality for showing more games from hidden container
    const gameElements = hiddenGames.querySelectorAll('.game-row');
    let count = 0;
    
    for (let i = 0; i < gameElements.length && count < 10; i++) {
        const game = gameElements[i];
        gamesContainer.insertBefore(game, button.parentElement);
        count++;
    }
    
    // Update the offset
    const newOffset = offset + count;
    button.setAttribute('data-offset', newOffset);
    
    // Get the total games count (either filtered or total)
    const totalGames = parseInt(container.getAttribute('data-filtered-games') || 
                               container.getAttribute('data-total-games'));
    
    // Hide the "Show More" button if all games are displayed
    if (newOffset >= totalGames) {
        button.parentElement.style.display = 'none';
    }
}

/**
 * Reorganize games in a tournament based on filtering
 * @param {HTMLElement} tournamentGroup - The tournament container
 * @param {Array} visibleGameElements - Array of visible game elements
 * @param {Array} hiddenGameElements - Array of hidden game elements
 */
function reorganizeGames(tournamentGroup, visibleGameElements, hiddenGameElements) {
    const gamesContainer = tournamentGroup.querySelector('.games-container');
    const hiddenGamesContainer = tournamentGroup.querySelector('.hidden-games');
    const showMoreContainer = tournamentGroup.querySelector('.show-more-container');
    
    if (!gamesContainer || !hiddenGamesContainer || !showMoreContainer) {
        return;
    }
    
    // Move all visible games to the main container (up to 10)
    const visibleToShow = visibleGameElements.slice(0, 10);
    const visibleToHide = visibleGameElements.slice(10);
    
    // Clear the containers
    while (gamesContainer.firstChild) {
        if (gamesContainer.firstChild.classList && 
            gamesContainer.firstChild.classList.contains('show-more-container')) {
            break;
        }
        gamesContainer.removeChild(gamesContainer.firstChild);
    }
    
    hiddenGamesContainer.innerHTML = '';
    
    // Add visible games to main container
    visibleToShow.forEach(game => {
        gamesContainer.insertBefore(game, showMoreContainer);
    });
    
    // Add remaining visible games to hidden container
    visibleToHide.forEach(game => {
        hiddenGamesContainer.appendChild(game);
    });
    
    // Add hidden games to hidden container
    hiddenGameElements.forEach(game => {
        hiddenGamesContainer.appendChild(game);
    });
    
    // Update show more button visibility based on whether there are more games to show
    const showMoreBtn = showMoreContainer.querySelector('.show-more-btn');
    if (showMoreBtn) {
        showMoreBtn.setAttribute('data-offset', '10');
        
        // Store the filtered games count for later use
        if (visibleGameElements.length > 0) {
            tournamentGroup.setAttribute('data-filtered-games', visibleGameElements.length.toString());
        } else {
            tournamentGroup.removeAttribute('data-filtered-games');
        }
        
        // Only show the button if there are more visible games to show
        showMoreContainer.style.display = visibleToHide.length > 0 ? '' : 'none';
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
        
        // Restore original tournament counts
        document.querySelectorAll('.tournament-container').forEach(tournamentGroup => {
            const totalGames = parseInt(tournamentGroup.getAttribute('data-total-games') || '0');
            const tournamentNameEl = tournamentGroup.querySelector('.tournament-name');
            if (tournamentNameEl) {
                const tournamentName = tournamentNameEl.textContent.split('(')[0].trim();
                tournamentNameEl.textContent = `${tournamentName} (${totalGames})`;
            }
            
            // Make sure all games containers are visible
            const gamesContainer = tournamentGroup.querySelector('.games-container');
            if (gamesContainer) {
                gamesContainer.style.display = 'block';
            }
            
            // Reset the tournament to its original state
            tournamentGroup.removeAttribute('data-filtered-games');
            
            // Get all games and reorganize them
            const allGames = Array.from(tournamentGroup.querySelectorAll('.game-row-interactive'));
            reorganizeGames(tournamentGroup, allGames, []);
        });
        
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
        
        return; // Exit early since we've shown all games
    }
    
    // For specific filters (not "all")
    gameElements.forEach(gameEl => {
        const gameFormat = gameEl.getAttribute('data-format');
        const gameVariant = gameEl.getAttribute('data-variant');
        
        if (isVariant) {
            // For Chess960, filter by variant
            if (gameVariant && gameVariant.toLowerCase() === filterValue.toLowerCase()) {
                gameEl.style.display = '';
                visibleGamesCount++;
            } else {
                gameEl.style.display = 'none';
            }
        } else {
            // For other formats, filter by format
            if (gameFormat && gameFormat.toLowerCase() === filterValue) {
                gameEl.style.display = '';
                visibleGamesCount++;
            } else {
                gameEl.style.display = 'none';
            }
        }
    });

    // Check if any games are visible in each tournament and update counts
    const tournamentContainers = document.querySelectorAll('.tournament-container');
    let anyTournamentVisible = false;
    
    tournamentContainers.forEach(tournamentGroup => {
        // Make sure we're selecting the correct elements within this tournament group
        const allGames = Array.from(tournamentGroup.querySelectorAll('.game-row-interactive'));
        const visibleGameElements = allGames.filter(game => game.style.display !== 'none');
        const hiddenGameElements = allGames.filter(game => game.style.display === 'none');
        const visibleGames = visibleGameElements.length;
        
        const tournamentNameEl = tournamentGroup.querySelector('.tournament-name');
        
        if (visibleGames === 0) {
            tournamentGroup.style.display = 'none';
        } else {
            tournamentGroup.style.display = '';
            anyTournamentVisible = true;
            
            // Make sure the games container is visible
            const gamesContainer = tournamentGroup.querySelector('.games-container');
            if (gamesContainer) {
                gamesContainer.style.display = 'block';
            }
            
            // Update the count to show only filtered games
            if (tournamentNameEl) {
                // Extract the tournament name and update with new count
                const tournamentName = tournamentNameEl.textContent.split('(')[0].trim();
                tournamentNameEl.textContent = `${tournamentName} (${visibleGames})`;
            }
            
            // Use the reorganizeGames function to handle the game elements
            reorganizeGames(tournamentGroup, visibleGameElements, hiddenGameElements);
        }
    });
    
    // Show "No games found" message if no tournaments are visible
    const eventsContainer = document.querySelector('.events-container');
    
    if (!anyTournamentVisible) {
        // Check if a "no games" message already exists
        const existingNoGamesMessage = document.querySelector('.no-filtered-games-message, .no-games-message');
        
        if (existingNoGamesMessage) {
            // Update existing message
            const messageParagraph = existingNoGamesMessage.querySelector('p');
            if (messageParagraph) {
                messageParagraph.textContent = 'No games found';
            }
        } else {
            // Create new message
            const noGamesMessage = document.createElement('div');
            noGamesMessage.className = 'p-3 text-center no-filtered-games-message';
            noGamesMessage.innerHTML = '<p>No games found</p>';
            
            // Add the new message
            eventsContainer.appendChild(noGamesMessage);
        }
    }
}

// Make functions globally available
window.toggleTournament = toggleTournament;
window.showMoreGames = showMoreGames;
window.filterGames = filterGames;
