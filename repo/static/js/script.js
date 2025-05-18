import LichessPgnViewer from '/static/viewer/viewer.js';

// Global variables
let pgnViewerInstance = null;
let gamePgnPositionParent = null; // This will store the direct parent of #gamePgnPosition, which is .board-container
let pgnCache = {};
let currentPgnForViewer = null;
let showMovesEnabled; // Initialized in DOMContentLoaded from localStorage

// Updated function signature and logic
function initializeOrUpdateViewer(pgnData, showMovesVal) { // showMovesVal will be 'auto' or false
    // 1. Identify and cache the static parent container (.board-container) for the PGN viewer.
    // This should only need to be found once.
    if (!gamePgnPositionParent || !document.body.contains(gamePgnPositionParent)) {
        gamePgnPositionParent = document.querySelector('.board-container'); // From game_display.html
        if (!gamePgnPositionParent) {
            console.error("PGN viewer's main parent container (.board-container) not found. Cannot initialize viewer.");
            return;
        }
    }

    // 2. Destroy existing PGN viewer instance, if any.
    if (pgnViewerInstance && pgnViewerInstance.destroy) {
        try {
            pgnViewerInstance.destroy();
        } catch (e) {
            // console.warn("Error destroying previous PGN viewer instance:", e);
        }
        pgnViewerInstance = null;
    }

    // 3. Aggressively clear the content of the parent container.
    // This removes the old #gamePgnPosition and any other remnants.
    if (gamePgnPositionParent) {
        gamePgnPositionParent.innerHTML = '';
    } else {
        // This case should be prevented by the check in step 1.
        // console.error("gamePgnPositionParent is not defined, cannot clear for new viewer.");
        return;
    }

    // 4. Create and append a new #gamePgnPosition DOM element inside the cleaned parent.
    const newViewerDomElement = document.createElement('div');
    newViewerDomElement.id = 'gamePgnPosition'; // Critical: Must have this ID
    newViewerDomElement.className = 'game-position'; // Match class from game_display.html for styling
    gamePgnPositionParent.appendChild(newViewerDomElement);

    // 5. Initialize the PGN viewer on the NEW element.
    const noPgnText = "PGN not available for this game.";

    if (pgnData) {
        try {
            pgnViewerInstance = LichessPgnViewer(newViewerDomElement, {
                pgn: pgnData,
                showMoves: showMovesVal, // Receives 'auto' or false directly
                keyboardToMove: true,
                initialPly: 0,
                showPlayers: true,
                showClocks: true,
                showControls: true,
                orientation: undefined,
            });
        } catch (e) {
            // console.error("Error initializing PGN viewer:", e);
            newViewerDomElement.innerHTML = `<p class="text-center p-3 text-muted">Error loading PGN viewer.</p>`;
        }
    } else {
        newViewerDomElement.innerHTML = `<p class="text-center p-3 text-muted">${noPgnText}</p>`;
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

// Function to update board container class based on showMovesEnabled state
function updateBoardContainerClass() {
    const boardContainer = document.getElementById('boardContainer');
    if (boardContainer) {
        if (showMovesEnabled) { // showMovesEnabled is the boolean state
            // Moves are shown, board container should be wider or default
            boardContainer.classList.remove('col-md-9', 'mx-auto');
            boardContainer.classList.add('col-md-12');
        } else {
            // Moves are hidden, board container should be narrower
            boardContainer.classList.remove('col-md-12');
            boardContainer.classList.add('col-md-9', 'mx-auto');
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    // DOM elements
    const gamesSectionWrapper = document.getElementById('gamesSectionWrapper');
    const gameDisplayWrapper = document.getElementById('gameDisplayWrapper');
    const gameLoader = document.getElementById('gameLoader');

    // Settings Dropdown Toggles
    const themeToggleDropdown = document.getElementById('themeToggleDropdown');
    const showMovesToggleDropdown = document.getElementById('showMovesToggleDropdown');

    // Initialize showMovesEnabled from localStorage before using it
    // Default to true if not found in localStorage
    const savedShowMoves = localStorage.getItem('showMovesEnabled');
    showMovesEnabled = savedShowMoves === 'false' ? false : true;

    // Initialize theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
    }
    
    // Only update visuals and add event listeners if elements exist
    if (themeToggleDropdown) {
        // Update theme toggle visuals
        const themeIcon = themeToggleDropdown.querySelector('.toggle-switch i');
        const themeText = themeToggleDropdown.querySelector('.theme-mode-text');
        
        if (themeText) themeText.textContent = 'Dark Mode'; // Keep text consistent
        
        if (themeIcon) {
            if (document.body.classList.contains('dark-mode')) {
                themeIcon.classList.remove('bi-toggle-off');
                themeIcon.classList.add('bi-toggle-on');
            } else {
                themeIcon.classList.remove('bi-toggle-on');
                themeIcon.classList.add('bi-toggle-off');
            }
        }
        
        // Add theme toggle event listener
        themeToggleDropdown.addEventListener('click', function (e) {
            e.preventDefault();
            document.body.classList.toggle('dark-mode');
            localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
            
            // Update visuals after click
            const icon = this.querySelector('.toggle-switch i');
            if (icon) {
                if (document.body.classList.contains('dark-mode')) {
                    icon.classList.remove('bi-toggle-off');
                    icon.classList.add('bi-toggle-on');
                } else {
                    icon.classList.remove('bi-toggle-on');
                    icon.classList.add('bi-toggle-off');
                }
            }
        });
    }

    if (showMovesToggleDropdown) {
        // Update show moves toggle visuals
        const movesIcon = showMovesToggleDropdown.querySelector('.toggle-switch i');
        const movesText = showMovesToggleDropdown.querySelector('.show-moves-text');
        
        if (movesText) movesText.textContent = 'Show Moves'; // Keep text consistent
        
        if (movesIcon) {
            if (showMovesEnabled) {
                movesIcon.classList.remove('bi-toggle-off');
                movesIcon.classList.add('bi-toggle-on');
            } else {
                movesIcon.classList.remove('bi-toggle-on');
                movesIcon.classList.add('bi-toggle-off');
            }
        }
        
        // Add show moves toggle event listener
        showMovesToggleDropdown.addEventListener('click', function (e) {
            e.preventDefault();
            showMovesEnabled = !showMovesEnabled;
            localStorage.setItem('showMovesEnabled', showMovesEnabled.toString());
            
            // Update visuals after click
            const icon = this.querySelector('.toggle-switch i');
            if (icon) {
                if (showMovesEnabled) {
                    icon.classList.remove('bi-toggle-off');
                    icon.classList.add('bi-toggle-on');
                } else {
                    icon.classList.remove('bi-toggle-on');
                    icon.classList.add('bi-toggle-off');
                }
            }
            
            updateBoardContainerClass();
            if (currentPgnForViewer) {
                initializeOrUpdateViewer(currentPgnForViewer, showMovesEnabled ? 'auto' : false);
            }
        });
    }
    
    // Update board container class based on current state
    updateBoardContainerClass();

    // calendar elements
    const calendarToggle = document.getElementById('calendarToggle');
    const calendarDropdown = document.getElementById('calendarDropdown');
    const datepickerContainer = document.querySelector('.datepicker-container');
    if (calendarToggle && calendarDropdown && datepickerContainer) {
        // Initialize datepicker
        $(datepickerContainer).datepicker({
            format: 'mm/dd/yy',
            autoclose: true,
            todayHighlight: true,
            orientation: 'bottom'
        });
        
        // Handle date selection
        $(datepickerContainer).on('changeDate', function(e) {
            const date = e.format('mm/dd/yy');
            window.location.href = `?date=${date}`;
        });
        
        // Toggle calendar dropdown
        calendarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            calendarDropdown.classList.toggle('show');
        });
        
        // Close calendar when clicking outside
        document.addEventListener('click', function(e) {
            if (!calendarToggle.contains(e.target) && !calendarDropdown.contains(e.target)) {
                calendarDropdown.classList.remove('show');
            }
        });
    }
    
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
            currentPgnForViewer = gameData.pgn;
    
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
            
            // Initialize PGN viewer - pass 'auto' or false based on showMovesEnabled
            initializeOrUpdateViewer(currentPgnForViewer, showMovesEnabled ? 'auto' : false);
            updateBoardContainerClass(); // Ensure class is correct after loading game
            
            showGameDetails();
        } else {
            currentPgnForViewer = null; // Clear PGN if loading failed
            // Initialize PGN viewer with null PGN, pass 'auto' or false for moves display
            initializeOrUpdateViewer(null, showMovesEnabled ? 'auto' : false);
            updateBoardContainerClass(); // Ensure class is correct even if PGN fails
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

// document.addEventListener('click', function(e) { // This listener seems problematic
//     const gamePgnPosition = document.getElementById('gamePgnPosition');
//     const toggleMovesLink = document.getElementById('toggleMovesLink'); // toggleMovesLink needs to be accessible here

//     if (gamePgnPosition && currentPgnForViewer) { // Check currentPgnForViewer as well
//         // This will re-initialize the viewer on ANY click on the document.
//         // This is likely not the intended behavior.
//         // initializeOrUpdateViewer(gamePgnPosition, currentPgnForViewer, showMovesState);
//     }

//     // Update the link text based on the new state
//     // This also might not be what you want on every click.
//     if (toggleMovesLink) {
//         // toggleMovesLink.textContent = showMovesState ? 'Hide Moves' : 'Show Moves'; // Old logic
//         toggleMovesLink.textContent = (showMovesState === 'auto') ? 'Hide Moves' : 'Show Moves'; // Corrected logic
//     }
// });

// The event listener `document.addEventListener('click', ...)` at the end of your script
// was likely added by mistake or for debugging. It causes the PGN viewer to re-initialize
// on *every* click anywhere on the page, which is generally not desired.
// I've commented it out above. If you need its functionality, it should be revised
// to target specific elements or events, and ensure `toggleMovesLink` is correctly scoped.
// For now, the primary toggle functionality is handled by the click listener on 'toggleMovesLink' itself.

// If you intended for the last click listener to be active, ensure `toggleMovesLink` is accessible
// (e.g., by querying it inside that listener or declaring it in a broader scope)
// and be aware that it will re-initialize the viewer on every document click.
// The corrected text update for it would be:
// if (toggleMovesLink) {
//     toggleMovesLink.textContent = (showMovesState === 'auto') ? 'Hide Moves' : 'Show Moves';
// }
// However, I strongly recommend removing or rethinking that general document click listener.
// The specific click listener for 'toggleMovesLink' is now correctly placed within DOMContentLoaded
// and handles the toggling.
