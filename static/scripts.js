// 🎮 Object Quest - Gamified Learning System
// Complete game management with points, leaderboard, and kid-friendly features

let objectData = {};
let activeModels = {}; // Track active object cards
let detectionDebounceTimer = null;
let detectedObjects = new Set(); // Track unique detected objects
let userScore = 0;
let userName = '';
let gameStarted = false;
let cameraActive = false; // Track camera state
let detectionLoopId = null; // Track detection loop

// 🎯 Enhanced Game Data Loading with Server Integration
function loadGameData() {
    userName = localStorage.getItem('userName') || '';
    userScore = parseInt(localStorage.getItem('userScore')) || 0;
    
    if (userName) {
        // Try to get updated score from server
        fetchPlayerDataFromServer(userName).then(serverData => {
            if (serverData && serverData.success) {
                const serverScore = serverData.player.score;
                if (serverScore > userScore) {
                    console.log(`🔄 Updating score from server: ${userScore} → ${serverScore}`);
                    userScore = serverScore;
                    localStorage.setItem('userScore', userScore.toString());
                }
            }
        }).catch(error => {
            console.log('📱 Using local data (server unavailable)');
        }).finally(() => {
            showGameInterface();
        });
    } else {
        // New user, show welcome screen
        showWelcomeScreen();
    }
}

function saveGameData() {
    localStorage.setItem('userName', userName);
    localStorage.setItem('userScore', userScore.toString());
    
    // Also try to update server in background
    if (userName) {
        updateLeaderboard(userName, userScore, 1, detectedObjects.size).catch(error => {
            console.log('📱 Server update failed, data saved locally');
        });
    }
}

// Fetch player data from server
async function fetchPlayerDataFromServer(name) {
    try {
        const response = await fetch(`/api/leaderboard/player/${encodeURIComponent(name)}`);
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.log('📱 Server unavailable for player data');
    }
    return null;
}

// 🎮 Welcome Screen Management
function showWelcomeScreen() {
    const welcomeScreen = document.getElementById('welcome-screen');
    const gameInterface = document.getElementById('game-interface');
    
    welcomeScreen.classList.remove('hidden');
    gameInterface.classList.add('hidden');
    gameStarted = false;
}

function showGameInterface() {
    const welcomeScreen = document.getElementById('welcome-screen');
    const gameInterface = document.getElementById('game-interface');
    const playerNameDisplay = document.getElementById('player-name-display');
    const currentScoreDisplay = document.getElementById('current-score');
    
    welcomeScreen.classList.add('hidden');
    gameInterface.classList.remove('hidden');
    gameStarted = true;
    
    playerNameDisplay.textContent = userName;
    currentScoreDisplay.textContent = userScore;
}

function stopCurrentSpeech() {
    if (window.speechSynthesis) {
        speechSynthesis.cancel();
        // Reset all speak buttons to their original state
        const speakBtns = document.querySelectorAll('.speak-btn');
        speakBtns.forEach(btn => {
            btn.innerHTML = '🔊 Tell me about this!';
            btn.disabled = false;
            btn.removeAttribute('data-speaking');
        });
    }
}

function logout() {
    if (confirm('Are you sure you want to logout? Your current session data will be cleared.')) {
        // Clear all game data
        localStorage.removeItem('userName');
        localStorage.removeItem('userScore');
        localStorage.removeItem('detectedObjects');
        localStorage.removeItem('leaderboard');
        
        // Reset all game variables
        userName = '';
        userScore = 0;
        detectedObjects = new Set();
        activeModels = {};
        gameStarted = false;
        
        // Clear any active camera stream
        const video = document.getElementById('video');
        if (video && video.srcObject) {
            video.srcObject.getTracks().forEach(track => track.stop());
            video.srcObject = null;
        }
        
        // Hide game interface and show welcome screen
        showWelcomeScreen();
        
        // Stop any current speech
        stopCurrentSpeech();
        
        console.log('User logged out successfully');
    }
}

// 🎯 Start Game Handler
function startGame() {
    const nameInput = document.getElementById('player-name');
    const name = nameInput.value.trim();
    
    if (name.length < 2) {
        // Add shake animation for invalid name
        nameInput.classList.add('animate-pulse');
        nameInput.style.border = '3px solid #ff6b6b';
        setTimeout(() => {
            nameInput.classList.remove('animate-pulse');
            nameInput.style.border = 'none';
        }, 1000);
        return;
    }
    
    userName = name;
    saveGameData();
    showGameInterface();
}

// 🏆 Leaderboard Management with SQLite Backend + LocalStorage Fallback
let useLocalStorageFallback = false;
let leaderboardCache = [];
let leaderboardRefreshInterval = null;

// API-based leaderboard functions with fallback
async function updateLeaderboard(name, score, gamesPlayed = 1, objectsDiscovered = 1) {
    let wasNewPlayer = false;
    
    // Try API first
    if (!useLocalStorageFallback) {
        try {
            const response = await fetch('/api/leaderboard', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    score: score,
                    games_played: gamesPlayed,
                    objects_discovered: objectsDiscovered
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    console.log('✅ Leaderboard updated via API');
                    // Check if this was a new player by comparing with cache
                    const existingInCache = leaderboardCache.find(p => p.name.toLowerCase() === name.toLowerCase());
                    wasNewPlayer = !existingInCache;
                    return result.player;
                } else {
                    throw new Error(result.error || 'API update failed');
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.warn('⚠️ API unavailable, falling back to localStorage:', error.message);
            useLocalStorageFallback = true;
        }
    }
    
    // Fallback to localStorage
    console.log('📱 Using localStorage fallback for leaderboard');
    let leaderboard = JSON.parse(localStorage.getItem('leaderboard')) || [];
    
    // Find existing player (case-insensitive comparison for fallback)
    const existing = leaderboard.find(player => player.name.toLowerCase() === name.toLowerCase());
    if (existing) {
        existing.score = Math.max(existing.score, score);
        existing.games_played = (existing.games_played || 0) + gamesPlayed;
        existing.objects_discovered = Math.max(existing.objects_discovered || 0, objectsDiscovered);
        // Preserve original casing if it was different
        if (existing.name !== name) {
            existing.name = name;
        }
    } else {
        wasNewPlayer = true;
        leaderboard.push({
            name,
            score,
            games_played: gamesPlayed,
            objects_discovered: objectsDiscovered
        });
    }
    
    leaderboard.sort((a, b) => b.score - a.score);
    leaderboard = leaderboard.slice(0, 20);
    localStorage.setItem('leaderboard', JSON.stringify(leaderboard));
    
    // Calculate rank locally
    const rank = leaderboard.findIndex(p => p.name.toLowerCase() === name.toLowerCase()) + 1;
    return {
        name,
        score,
        rank,
        total_players: leaderboard.length,
        games_played: gamesPlayed,
        objects_discovered: objectsDiscovered,
        wasNewPlayer
    };
}

async function showLeaderboard() {
    const modal = document.getElementById('leaderboard-modal');
    const content = document.getElementById('leaderboard-content');
    
    // Show loading state
    content.innerHTML = `
        <div class="text-center py-8">
            <div class="text-6xl mb-4 animate-spin">🏆</div>
            <p class="text-gray-500 text-lg">Loading leaderboard...</p>
        </div>
    `;
    
    modal.classList.remove('hidden');
    
    // Clear any existing refresh interval
    if (leaderboardRefreshInterval) {
        clearInterval(leaderboardRefreshInterval);
        leaderboardRefreshInterval = null;
    }
    
    let players = [];
    let totalPlayers = 0;
    
    // Try API first
    if (!useLocalStorageFallback) {
        try {
            const response = await fetch('/api/leaderboard?limit=10');
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    players = result.players;
                    totalPlayers = result.total_players;
                    leaderboardCache = players; // Update cache
                    console.log('✅ Leaderboard loaded via API');
                } else {
                    throw new Error(result.error || 'API response error');
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.warn('⚠️ API unavailable, falling back to localStorage:', error.message);
            useLocalStorageFallback = true;
        }
    }
    
    // Fallback to localStorage
    if (useLocalStorageFallback) {
        console.log('📱 Using localStorage fallback for leaderboard display');
        players = JSON.parse(localStorage.getItem('leaderboard')) || [];
        totalPlayers = players.length;
        leaderboardCache = players;
    }
    
    // Render leaderboard
    if (players.length === 0) {
        content.innerHTML = `
            <div class="text-center py-8">
                <div class="text-6xl mb-4">🏆</div>
                <p class="text-gray-500 text-lg">No players yet! Be the first to play!</p>
                <p class="text-sm text-gray-400 mt-2">${useLocalStorageFallback ? '(Using offline mode)' : ''}</p>
            </div>
        `;
    } else {
        const topPlayers = players.slice(0, 5);
        content.innerHTML = topPlayers.map((player, index) => {
            const rankEmoji = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '🏅';
            const rowClass = index === 0 ? 'bg-gradient-to-r from-yellow-100 to-yellow-200 border-yellow-300' :
                           index === 1 ? 'bg-gradient-to-r from-gray-100 to-gray-200 border-gray-300' :
                           index === 2 ? 'bg-gradient-to-r from-orange-100 to-orange-200 border-orange-300' :
                           'bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200';
            
            // Highlight current user
            const isCurrentUser = player.name.toLowerCase() === userName.toLowerCase();
            const userHighlight = isCurrentUser ? 'ring-4 ring-green-400 ring-opacity-75' : '';
            
            return `
                <div class="flex items-center justify-between p-4 rounded-2xl border-2 ${rowClass} shadow-lg ${userHighlight} transition-all duration-300">
                    <div class="flex items-center space-x-3">
                        <span class="text-2xl">${rankEmoji}</span>
                        <span class="text-xl font-bold text-purple-600">#${index + 1}</span>
                        <span class="text-lg font-semibold text-gray-700">${player.name}</span>
                        ${isCurrentUser ? '<span class="text-sm bg-green-400 text-white px-2 py-1 rounded-full">YOU</span>' : ''}
                    </div>
                    <div class="text-right">
                        <div class="text-xl font-bold text-green-600">${player.score} pts</div>
                        <div class="text-xs text-gray-500">
                            ${player.games_played || 1} games • ${player.objects_discovered || 1} objects
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        // Add footer with connection status and auto-refresh info
        const connectionStatus = useLocalStorageFallback
            ? '<div class="mt-4 p-2 bg-yellow-100 rounded-lg text-center text-sm text-yellow-700">📱 Offline Mode - Data saved locally</div>'
            : '<div class="mt-4 p-2 bg-green-100 rounded-lg text-center text-sm text-green-700">✅ Connected - Data saved to server</div>';
            
        // Add refresh button and auto-refresh info
        const refreshControls = `
            <div class="mt-4 flex items-center justify-center space-x-4">
                <button onclick="refreshLeaderboard()" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-bold transition-all">
                    🔄 Refresh Now
                </button>
                <div class="text-xs text-gray-500">
                    ${useLocalStorageFallback ? '' : 'Auto-refresh every 30 seconds'}
                </div>
            </div>
        `;
            
        content.innerHTML += connectionStatus + refreshControls;
    }
    
    // Start auto-refresh for API mode
    if (!useLocalStorageFallback && players.length > 0) {
        leaderboardRefreshInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/leaderboard?limit=10');
                if (response.ok) {
                    const result = await response.json();
                    if (result.success && result.players.length > players.length) {
                        console.log('📈 New player detected, refreshing leaderboard');
                        showLeaderboard(); // Re-render with new data
                    }
                }
            } catch (error) {
                console.log('Auto-refresh failed:', error.message);
            }
        }, 30000); // Check every 30 seconds
    }
}

// Manual refresh function
async function refreshLeaderboard() {
    console.log('🔄 Manually refreshing leaderboard...');
    
    // Clear cache to force fresh data
    leaderboardCache = [];
    
    // Re-fetch data
    await showLeaderboard();
    
    // Show confirmation
    const refreshBtn = document.querySelector('button[onclick="refreshLeaderboard()"]');
    if (refreshBtn) {
        const originalText = refreshBtn.innerHTML;
        refreshBtn.innerHTML = '✅ Updated!';
        refreshBtn.disabled = true;
        
        setTimeout(() => {
            refreshBtn.innerHTML = originalText;
            refreshBtn.disabled = false;
        }, 2000);
    }
}

function hideLeaderboard() {
    const modal = document.getElementById('leaderboard-modal');
    modal.classList.add('hidden');
    
    // Clear auto-refresh interval when closing
    if (leaderboardRefreshInterval) {
        clearInterval(leaderboardRefreshInterval);
        leaderboardRefreshInterval = null;
    }
}


// 🎉 Confetti Animation for Points
function celebratePoints() {
    const duration = 1000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

    function randomInRange(min, max) {
        return Math.random() * (max - min) + min;
    }

    const interval = setInterval(() => {
        const timeLeft = animationEnd - Date.now();

        if (timeLeft <= 0) {
            return clearInterval(interval);
        }

        const particleCount = 50 * (timeLeft / duration);

        confetti({
            ...defaults,
            particleCount,
            origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 }
        });
        confetti({
            ...defaults,
            particleCount,
            origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 }
        });
    }, 250);
}

// 💎 Points System
function awardPointsForNewObject(className) {
    if (!detectedObjects.has(className)) {
        detectedObjects.add(className);
        
        // Award 10 points for first time detection
        userScore += 10;
        saveGameData();
        updateScoreDisplay();
        
        // Update leaderboard with discovered objects count
        const discoveredCount = detectedObjects.size;
        updateLeaderboard(userName, userScore, 1, discoveredCount);
        
        // Show confetti celebration
        celebratePoints();
        
        // Show "+10" animation
        showPointsAnimation();
    }
}

function updateScoreDisplay() {
    const scoreDisplay = document.getElementById('current-score');
    scoreDisplay.textContent = userScore;
    
    // Add glow effect to score badge
    const scoreBadge = document.getElementById('score-badge');
    scoreBadge.classList.add('animate-pulse');
    setTimeout(() => {
        scoreBadge.classList.remove('animate-pulse');
    }, 1000);
}

function showPointsAnimation() {
    // Create floating +10 points animation
    const pointsAnimation = document.createElement('div');
    pointsAnimation.innerHTML = '+10 Points! 🎉';
    pointsAnimation.className = 'fixed top-20 right-20 text-2xl font-bold text-green-600 bg-white/90 px-4 py-2 rounded-full shadow-lg animate-bounce z-50';
    pointsAnimation.style.animation = 'floatUp 2s ease-out forwards';
    
    // Add CSS animation keyframes
    if (!document.querySelector('#points-animation-styles')) {
        const style = document.createElement('style');
        style.id = 'points-animation-styles';
        style.textContent = `
            @keyframes floatUp {
                0% {
                    transform: translateY(0) scale(0.5);
                    opacity: 1;
                }
                50% {
                    transform: translateY(-50px) scale(1.2);
                    opacity: 1;
                }
                100% {
                    transform: translateY(-100px) scale(0.8);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(pointsAnimation);
    
    setTimeout(() => {
        pointsAnimation.remove();
    }, 2000);
}

// 📱 Camera Control Functions
function toggleCamera() {
    if (cameraActive) {
        stopCamera();
    } else {
        startCamera();
    }
}

function startCamera() {
    const video = document.getElementById('video');
    const videoContainer = document.getElementById('video-container');
    const cameraBtn = document.getElementById('camera-toggle-btn');
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.warn('Camera not supported');
        cameraBtn.textContent = '📹 Camera Not Supported';
        cameraBtn.disabled = true;
        return;
    }
    
    cameraBtn.textContent = '📹 Starting Camera...';
    cameraBtn.disabled = true;
    
    navigator.mediaDevices.getUserMedia({
        video: {
            facingMode: 'environment',
            width: { ideal: 640 },
            height: { ideal: 480 }
        }
    }).then(stream => {
        video.srcObject = stream;
        videoContainer.classList.remove('hidden');
        cameraActive = true;
        
        // Update button state
        cameraBtn.textContent = '📹 Stop Camera';
        cameraBtn.disabled = false;
        
        // Set up video event listeners BEFORE video is loaded
        video.onloadedmetadata = () => {
            console.log('Video metadata loaded, starting detection');
            // Set overlay size and start object detection
            const overlay = document.getElementById('overlay');
            overlay.width = video.videoWidth;
            overlay.height = video.videoHeight;
            startObjectDetection();
        };
        
        video.onloadeddata = () => {
            console.log('Video data loaded');
        };
        
        video.oncanplay = () => {
            console.log('Video can play');
        };
        
        // If video is already loaded (stream starts quickly), start detection immediately
        if (video.readyState >= 2) { // HAVE_CURRENT_DATA
            console.log('Video already ready, starting detection');
            const overlay = document.getElementById('overlay');
            overlay.width = video.videoWidth;
            overlay.height = video.videoHeight;
            startObjectDetection();
        }
    }).catch(error => {
        console.error('Camera access denied:', error);
        cameraBtn.textContent = '📹 Start Camera';
        cameraBtn.disabled = false;
        
        // Show a message to user
        videoContainer.innerHTML = `
            <div class="flex items-center justify-center h-64 bg-red-100 border-2 border-red-300 rounded-2xl">
                <div class="text-center">
                    <div class="text-6xl mb-4">📷</div>
                    <p class="text-lg font-semibold text-red-600">Camera access needed for detection!</p>
                    <p class="text-sm text-red-500 mt-2">Please allow camera access to start detecting objects.</p>
                    <button
                        onclick="toggleCamera()"
                        class="mt-4 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg"
                    >
                        🔄 Try Again
                    </button>
                </div>
            </div>
        `;
        videoContainer.classList.remove('hidden');
    });
}

function stopCamera() {
    const video = document.getElementById('video');
    const videoContainer = document.getElementById('video-container');
    const cameraBtn = document.getElementById('camera-toggle-btn');
    
    // Stop camera stream
    if (video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
        video.srcObject = null;
    }
    
    // Stop detection loop
    if (detectionLoopId) {
        cancelAnimationFrame(detectionLoopId);
        detectionLoopId = null;
    }
    
    // Clear overlay
    const overlay = document.getElementById('overlay');
    if (overlay) {
        const ctx = overlay.getContext('2d');
        ctx.clearRect(0, 0, overlay.width, overlay.height);
    }
    
    // Hide video container
    videoContainer.classList.add('hidden');
    
    // Update state
    cameraActive = false;
    
    // Update button state
    cameraBtn.textContent = '📹 Start Camera';
    cameraBtn.disabled = false;
    
    console.log('Camera stopped');
}

// Legacy function for backward compatibility
function initializeCamera() {
    // Do nothing - camera is now manually controlled
}

// 🔍 Load object information from JSON file
async function loadObjectInfo() {
    try {
        const response = await fetch('/static/data/objects.json');
        objectData = await response.json();
    } catch (error) {
        console.error('Error loading object data:', error);
        objectData = {};
    }
}

// 🎯 Handle detection results with gamification
function handleDetections(detections, classNames) {
    if (detectionDebounceTimer) {
        clearTimeout(detectionDebounceTimer);
    }
    
    detectionDebounceTimer = setTimeout(() => {
        const detectedClasses = new Set(detections.map(det => classNames[det[5]]));
        
        // Award points for newly detected objects
        detectedClasses.forEach(cls => {
            awardPointsForNewObject(cls);
        });
        
        // Create cards for newly detected classes only
        detectedClasses.forEach(cls => {
            if (!activeModels[cls]) {
                createObjectCard(cls);
            }
        });
    }, 500);
}

// 🃏 Create object card (enhanced with gamification)
function createObjectCard(className) {
    const container = document.getElementById('models-container');
    const info = objectData[className];
    
    if (!info) {
        console.warn(`No educational data found for class: ${className}`);
        return;
    }
    
    // Create card wrapper with fun animations
    const card = document.createElement('div');
    card.className = 'object-card opacity-0 transform scale-90 transition-all duration-500 hover:scale-105';
    
    // Create 3D viewer container
    const viewerBox = document.createElement('div');
    viewerBox.className = 'viewer-box relative overflow-hidden rounded-2xl shadow-lg';
    
    // Create loading spinner
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner absolute inset-0 flex items-center justify-center bg-gradient-to-br from-blue-100 to-purple-100';
    spinner.innerHTML = `
        <div class="text-center">
            <div class="text-4xl animate-spin mb-2">⏳</div>
            <p class="text-lg font-semibold text-purple-600">Loading 3D Model...</p>
        </div>
    `;
    viewerBox.appendChild(spinner);
    
    // Create remove button
    const removeBtn = document.createElement('button');
    removeBtn.className = 'remove-btn absolute top-2 right-2 w-10 h-10 bg-red-400 hover:bg-red-500 text-white rounded-full shadow-lg transform hover:scale-110 transition-all duration-200 text-xl font-bold z-10';
    removeBtn.innerHTML = '❌';
    removeBtn.setAttribute('aria-label', `Remove ${info.displayName} card`);
    removeBtn.onclick = () => removeCard(className);
    
    // Create info section
    const infoSection = document.createElement('div');
    infoSection.className = 'p-4 space-y-3';
    
    // Object name with special styling
    const name = document.createElement('h3');
    name.textContent = info.displayName;
    name.className = 'text-2xl font-bold text-center text-purple-600 mb-2';
    
    // Description with emoji
    const desc = document.createElement('p');
    desc.textContent = info.desc;
    desc.className = 'text-gray-700 leading-relaxed';
    
    // Vocabulary section with fun styling
    const vocabSection = document.createElement('div');
    vocabSection.className = 'bg-gradient-to-r from-yellow-100 to-orange-100 p-3 rounded-xl border-2 border-yellow-200';
    const vocabTitle = document.createElement('h4');
    vocabTitle.textContent = '📚 More Words:';
    vocabTitle.className = 'text-lg font-bold text-orange-600 mb-2';
    const vocabList = document.createElement('p');
    vocabList.textContent = info.vocab.join(', ');
    vocabList.className = 'text-orange-700 font-medium';
    vocabSection.appendChild(vocabTitle);
    vocabSection.appendChild(vocabList);
    
    // Simple speak button
    const speakBtn = document.createElement('button');
    speakBtn.className = 'speak-btn w-full bg-gradient-to-r from-green-400 to-blue-500 hover:from-green-500 hover:to-blue-600 text-white font-bold py-3 px-6 rounded-xl shadow-lg transform hover:scale-105 transition-all duration-200';
    speakBtn.innerHTML = '🔊 Tell me about this!';
    speakBtn.setAttribute('data-speaking', 'false');
    speakBtn.setAttribute('aria-label', `Learn about ${info.displayName}`);
    speakBtn.onclick = () => speakCardInfo(info);
    
    // Combine information if available
    if (info.combines && info.combines.length > 0) {
        const combinesSection = document.createElement('div');
        combinesSection.className = 'bg-gradient-to-r from-pink-100 to-purple-100 p-3 rounded-xl border-2 border-pink-200';
        const combinesTitle = document.createElement('h4');
        combinesTitle.textContent = '🤝 Can combine with:';
        combinesTitle.className = 'text-lg font-bold text-purple-600 mb-2';
        const combinesList = document.createElement('p');
        combinesList.textContent = info.combines.join(', ');
        combinesList.className = 'text-purple-700 font-medium';
        combinesSection.appendChild(combinesTitle);
        combinesSection.appendChild(combinesList);
        infoSection.appendChild(combinesSection);
    }
    
    // Assemble card
    infoSection.appendChild(name);
    infoSection.appendChild(desc);
    infoSection.appendChild(vocabSection);
    infoSection.appendChild(speakBtn);
    
    card.appendChild(removeBtn);
    card.appendChild(viewerBox);
    card.appendChild(infoSection);
    
    container.appendChild(card);
    
    // Trigger fade-in animation
    setTimeout(() => {
        card.classList.remove('opacity-0', 'scale-90');
        card.classList.add('opacity-100', 'scale-100');
    }, 100);
    
    // Create 3D viewer
    const resources = createThreeViewerForCard(viewerBox, info.model, className);
    
    // Store card reference
    activeModels[className] = {
        card: card,
        resources: resources,
        info: info
    };
}

// 🎨 Enhanced Three.js viewer creation with better lighting and colors
function createThreeViewerForCard(viewerEl, modelPath, className) {
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
    
    // Enhanced renderer with better quality
    const renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
        preserveDrawingBuffer: false
    });
    
    renderer.setSize(viewerEl.clientWidth || 400, viewerEl.clientHeight || 400);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Limit for performance
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    viewerEl.appendChild(renderer.domElement);
    
    camera.position.set(0, 2, 4);
    
    // Enhanced multi-light setup for better colors
    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    
    // Main directional light
    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight1.position.set(5, 5, 5);
    dirLight1.castShadow = true;
    dirLight1.shadow.mapSize.width = 2048;
    dirLight1.shadow.mapSize.height = 2048;
    scene.add(dirLight1);
    
    // Fill light from opposite side
    const dirLight2 = new THREE.DirectionalLight(0x4FC3F7, 0.3);
    dirLight2.position.set(-3, 3, -2);
    scene.add(dirLight2);
    
    // Warm accent light
    const warmLight = new THREE.PointLight(0xFFB74D, 0.4, 10);
    warmLight.position.set(0, 2, 2);
    scene.add(warmLight);
    
    // Ground plane for shadows
    const planeGeometry = new THREE.PlaneGeometry(10, 10);
    const planeMaterial = new THREE.ShadowMaterial({ opacity: 0.15 });
    const plane = new THREE.Mesh(planeGeometry, planeMaterial);
    plane.rotation.x = -Math.PI / 2;
    plane.position.y = -2;
    plane.receiveShadow = true;
    scene.add(plane);
    
    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 2;
    controls.maxDistance = 8;
    controls.enablePan = true;
    
    const loader = new THREE.GLTFLoader();
    
    loader.load(
        modelPath,
        gltf => {
            const model = gltf.scene;
            
            // Enhanced model processing for better colors
            model.traverse((child) => {
                if (child.isMesh) {
                    // Improve material properties for better colors
                    if (child.material) {
                        if (child.material.isMeshPhongMaterial || child.material.isMeshStandardMaterial) {
                            child.material.needsUpdate = true;
                            child.material.smoothShading = true;
                            // Enhance material properties
                            child.material.emissive = child.material.emissive || new THREE.Color(0x000000);
                            child.material.emissiveIntensity = 0.1;
                        }
                    }
                    child.castShadow = true;
                    child.receiveShadow = true;
                }
            });
            
            // Auto-scale for visibility with better proportions
            const box = new THREE.Box3().setFromObject(model);
            const size = box.getSize(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z);
            
            if (maxDim > 0) {
                const scale = 2.0 / maxDim;
                model.scale.setScalar(scale);
            }
            
            model.position.set(0, -1.0, 0);
            scene.add(model);
            
            // Remove loading spinner
            const spinner = viewerEl.querySelector('.loading-spinner');
            if (spinner) {
                spinner.style.opacity = '0';
                setTimeout(() => spinner.remove(), 300);
            }
            
            // Auto-rotate with gentle movement
            let rotationSpeed = 0.003;
            const originalUpdate = controls.update.bind(controls);
            controls.update = function() {
                originalUpdate();
                model.rotation.y += rotationSpeed;
            };
        },
        undefined,
        err => {
            console.error(`Error loading model ${className}:`, err);
            
            // Remove loading spinner and show fallback
            const spinner = viewerEl.querySelector('.loading-spinner');
            if (spinner) {
                spinner.innerHTML = `
                    <div class="text-center">
                        <div class="text-4xl mb-2">🎲</div>
                        <p class="text-lg font-semibold text-purple-600">Loading colorful cube...</p>
                    </div>
                `;
                setTimeout(() => spinner.remove(), 2000);
            }
            
            // Create enhanced colorful fallback cube
            const geometry = new THREE.BoxGeometry(2, 2, 2);
            const materials = [
                new THREE.MeshPhongMaterial({ color: 0xFF6B6B }), // Red
                new THREE.MeshPhongMaterial({ color: 0x4ECDC4 }), // Teal
                new THREE.MeshPhongMaterial({ color: 0x45B7D1 }), // Blue
                new THREE.MeshPhongMaterial({ color: 0x96CEB4 }), // Green
                new THREE.MeshPhongMaterial({ color: 0xFFEAA7 }), // Yellow
                new THREE.MeshPhongMaterial({ color: 0xDDA0DD })  // Purple
            ];
            
            const cube = new THREE.Mesh(geometry, materials);
            cube.position.set(0, -1.0, 0);
            scene.add(cube);
            
            const originalUpdate = controls.update.bind(controls);
            controls.update = function() {
                originalUpdate();
                cube.rotation.y += 0.01;
                cube.rotation.x += 0.005;
            };
        }
    );
    
    const animate = () => {
        const animateId = requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
        return animateId;
    };
    
    const animateId = animate();
    
    return {
        scene: scene,
        camera: camera,
        renderer: renderer,
        controls: controls,
        animateId: animateId
    };
}

// 🗑️ Remove card with cleanup
function removeCard(className) {
    const cardData = activeModels[className];
    if (!cardData) return;
    
    // Add fade-out animation
    cardData.card.style.transform = 'scale(0.8)';
    cardData.card.style.opacity = '0';
    
    setTimeout(() => {
        if (cardData.card.parentNode) {
            cardData.card.parentNode.removeChild(cardData.card);
        }
        
        // Dispose Three.js resources
        disposeThreeResources(cardData.resources);
        
        // Remove from active models
        delete activeModels[className];
    }, 300);
}

// 🧹 Dispose Three.js resources
function disposeThreeResources(resources) {
    if (!resources) return;
    
    if (resources.animateId) {
        cancelAnimationFrame(resources.animateId);
    }
    
    if (resources.controls) {
        resources.controls.dispose();
    }
    
    if (resources.scene) {
        resources.scene.traverse((child) => {
            if (child.geometry) {
                child.geometry.dispose();
            }
            
            if (child.material) {
                if (Array.isArray(child.material)) {
                    child.material.forEach(material => {
                        if (material.map) material.map.dispose();
                        material.dispose();
                    });
                } else {
                    if (child.material.map) child.material.map.dispose();
                    child.material.dispose();
                }
            }
            
            if (child.texture) {
                child.texture.dispose();
            }
        });
    }
    
    if (resources.renderer) {
        resources.renderer.forceContextLoss();
    }
}

// 🔊 Simple text-to-speech
function speakCardInfo(info) {
    if (!window.speechSynthesis) {
        alert('Text-to-speech is not supported in your browser. Please use Chrome, Firefox, or Safari.');
        return;
    }
    
    speechSynthesis.cancel();
    
    const speakBtn = findSpeakButtonForInfo(info);
    if (!speakBtn) return;
    
    if (speakBtn.getAttribute('data-speaking') === 'true') {
        stopCurrentSpeech();
        return;
    }
    
    let textToSpeak = `This is a ${info.displayName}. ${info.desc} Learn more words: ${info.vocab.join(', ')}.`;
    if (info.combines && info.combines.length > 0) {
        textToSpeak += ` It can combine with: ${info.combines.join(' and ')}.`;
    }
    
    speakBtn.setAttribute('data-speaking', 'true');
    speakBtn.innerHTML = '⏹️ Stop Reading';
    speakBtn.disabled = false;
    
    const sentences = textToSpeak.split(/[.!?]+/).filter(s => s.trim().length > 0);
    let currentSentenceIndex = 0;
    
    function speakNextSentence() {
        if (currentSentenceIndex >= sentences.length) {
            speakBtn.setAttribute('data-speaking', 'false');
            speakBtn.innerHTML = '🔊 Tell me about this!';
            return;
        }
        
        const sentence = sentences[currentSentenceIndex].trim();
        const utterance = new SpeechSynthesisUtterance(sentence);
        
        const voices = speechSynthesis.getVoices();
        const voice = voices.find(v => v.lang.startsWith('en')) || voices[0];
        if (voice) {
            utterance.voice = voice;
        }
        
        utterance.lang = 'en-US';
        utterance.rate = 0.9;
        utterance.pitch = 1.1;
        utterance.volume = 1.0;
        
        if (sentence.includes(info.displayName)) {
            utterance.pitch = 1.2;
            utterance.rate = 0.85;
        }
        
        utterance.onend = () => {
            currentSentenceIndex++;
            setTimeout(speakNextSentence, 300);
        };
        
        utterance.onerror = (event) => {
            console.error('Speech synthesis error:', event.error);
            currentSentenceIndex++;
            setTimeout(speakNextSentence, 100);
        };
        
        speechSynthesis.speak(utterance);
    }
    
    speakNextSentence();
}

function stopCurrentSpeech() {
    speechSynthesis.cancel();
    
    Object.values(activeModels).forEach(cardData => {
        const speakBtn = cardData.card.querySelector('.speak-btn');
        if (speakBtn) {
            speakBtn.setAttribute('data-speaking', 'false');
            speakBtn.innerHTML = '🔊 Tell me about this!';
            speakBtn.disabled = false;
        }
    });
}

function findSpeakButtonForInfo(info) {
    for (const cardData of Object.values(activeModels)) {
        if (cardData.info === info) {
            return cardData.card.querySelector('.speak-btn');
        }
    }
    return null;
}

// 🎮 Start object detection loop
function startObjectDetection() {
    console.log('Starting object detection...');
    
    const video = document.getElementById('video');
    const overlay = document.getElementById('overlay');
    const ctx = overlay.getContext('2d');
    let lastProcessedTime = 0;
    const targetFPS = 2; // Reduced to 2 FPS for more reliable detection
    const frameInterval = 1000 / targetFPS;
    
    // Force set overlay size immediately
    const updateOverlaySize = () => {
        if (video.videoWidth > 0 && video.videoHeight > 0) {
            overlay.width = video.videoWidth;
            overlay.height = video.videoHeight;
            console.log(`Overlay size set to: ${overlay.width}x${overlay.height}`);
        }
    };
    
    updateOverlaySize(); // Try immediately
    
    // Set up video event listener to ensure overlay is sized correctly
    video.addEventListener('loadedmetadata', () => {
        console.log('Video metadata loaded for detection');
        updateOverlaySize();
    });
    
    // Set up video resize listener
    video.addEventListener('resize', updateOverlaySize);
    
    async function processFrame(currentTime) {
        // Continue processing if game is running and camera is active
        if (!gameStarted || !cameraActive) {
            detectionLoopId = requestAnimationFrame(processFrame);
            return;
        }
        
        // Check if video is ready
        if (!video.srcObject || video.videoWidth === 0 || video.videoHeight === 0) {
            console.log('Video not ready yet, waiting...');
            detectionLoopId = requestAnimationFrame(processFrame);
            return;
        }
        
        // Check frame rate limiting
        if (currentTime - lastProcessedTime < frameInterval) {
            detectionLoopId = requestAnimationFrame(processFrame);
            return;
        }
        
        lastProcessedTime = currentTime;
        
        try {
            // Create canvas from video frame
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const canvasCtx = canvas.getContext('2d');
            canvasCtx.drawImage(video, 0, 0);
            const imageData = canvas.toDataURL('image/jpeg', 0.5);
            
            // Send to server for detection
            const response = await fetch('/process_frame', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: imageData })
            });
            
            if (!response.ok) {
                console.error('Server processing failed:', response.status);
                detectionLoopId = requestAnimationFrame(processFrame);
                return;
            }
            
            const result = await response.json();
            
            // Clear previous detections
            ctx.clearRect(0, 0, overlay.width, overlay.height);
            
            // Draw detection status
            ctx.fillStyle = 'rgba(0, 255, 0, 0.8)';
            ctx.font = 'bold 16px Arial';
            ctx.fillText('🎯 Detection Active', 10, 25);
            
            // Process new detections
            if (result.detections && result.detections.length > 0) {
                console.log(`Found ${result.detections.length} detections`);
                
                // Draw bounding boxes with fun colors
                result.detections.forEach((detection, index) => {
                    const [x1, y1, x2, y2, conf, cls_id] = detection;
                    const label = result.class_names[cls_id] || `Class ${cls_id}`;
                    const color = getColor(cls_id);
                    
                    // Draw colorful bounding box
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 4;
                    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
                    
                    // Draw label with background
                    const text = `${label} ${(conf * 100).toFixed(1)}%`;
                    ctx.font = 'bold 16px Arial';
                    const textMetrics = ctx.measureText(text);
                    const textWidth = textMetrics.width;
                    const textHeight = 20;
                    
                    // Background for text
                    ctx.fillStyle = color;
                    ctx.fillRect(x1, Math.max(0, y1 - textHeight - 4), textWidth + 8, textHeight + 6);
                    
                    // White text
                    ctx.fillStyle = '#ffffff';
                    ctx.fillText(text, x1 + 4, Math.max(16, y1 - 6));
                    
                    console.log(`Detection ${index + 1}: ${label} (${(conf * 100).toFixed(1)}%)`);
                });
                
                // Handle gamification - create cards and award points
                handleDetections(result.detections, result.class_names);
            } else {
                // No detections - show status
                ctx.fillStyle = 'rgba(255, 0, 0, 0.8)';
                ctx.font = 'bold 16px Arial';
                ctx.fillText('🔍 Looking for objects...', 10, 25);
                console.log('No objects detected in this frame');
            }
        } catch (error) {
            console.error('Error processing frame:', error);
            // Don't stop the loop due to network errors
        }
        
        // Continue the detection loop
        detectionLoopId = requestAnimationFrame(processFrame);
    }
    
    // Start the detection loop and store the ID
    console.log('Detection loop started');
    detectionLoopId = requestAnimationFrame(processFrame);
}

function getColor(classId) {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FFB347', '#98D8C8'];
    return colors[classId % colors.length];
}

// 🧪 Test Detection Function (for debugging)
async function testDetection() {
    const video = document.getElementById('video');
    const statusText = document.getElementById('detection-status-text');
    
    if (!video.srcObject || video.videoWidth === 0) {
        statusText.textContent = '❌ Camera not ready for testing';
        return;
    }
    
    statusText.textContent = '🧪 Testing detection...';
    
    try {
        // Create a test frame from current video
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);
        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        
        console.log('Sending test frame to server...');
        
        const response = await fetch('/process_frame', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: imageData })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Test detection result:', result);
        
        if (result.detections && result.detections.length > 0) {
            statusText.textContent = `✅ Backend Working! Found ${result.detections.length} objects`;
            console.log('Backend is working correctly!');
        } else {
            statusText.textContent = '⚠️ Backend Working, No objects detected';
            console.log('Backend is working but no objects found in test frame');
        }
        
        // Show detected classes
        if (result.detections && result.detections.length > 0) {
            const detected = result.detections.map(det => {
                const label = result.class_names[det[5]] || `Class ${det[5]}`;
                return `${label} (${(det[4] * 100).toFixed(1)}%)`;
            });
            console.log('Detected objects:', detected.join(', '));
        }
        
    } catch (error) {
        console.error('Test detection failed:', error);
        statusText.textContent = `❌ Backend Error: ${error.message}`;
    }
    
    // Reset status after 3 seconds
    setTimeout(() => {
        statusText.textContent = '📷 Camera Active - Ready to Detect!';
    }, 3000);
}

// 🔄 Update Detection Status
function updateDetectionStatus(message, isError = false) {
    const statusText = document.getElementById('detection-status-text');
    if (statusText) {
        statusText.textContent = message;
        statusText.className = isError
            ? 'text-lg font-bold text-red-600'
            : 'text-lg font-bold text-purple-600';
    }
}

// 🎯 Initialize the game
document.addEventListener('DOMContentLoaded', function() {
    // Load game data
    loadGameData();
    loadObjectInfo();
    
    // Event listeners
    document.getElementById('start-game-btn').addEventListener('click', startGame);
    document.getElementById('camera-toggle-btn').addEventListener('click', toggleCamera);
    document.getElementById('leaderboard-btn').addEventListener('click', showLeaderboard);
    document.getElementById('logout-btn').addEventListener('click', logout);
    document.getElementById('close-leaderboard').addEventListener('click', hideLeaderboard);
    
    // Add test detection button listener
    const testBtn = document.getElementById('test-detect-btn');
    if (testBtn) {
        testBtn.addEventListener('click', testDetection);
        console.log('Test detection button ready');
    }
    
    // Enter key support for name input
    document.getElementById('player-name').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            startGame();
        }
    });
    
    // Close leaderboard when clicking outside
    document.getElementById('leaderboard-modal').addEventListener('click', function(e) {
        if (e.target === this) {
            hideLeaderboard();
        }
    });
    
    // Initialize voice system
    if ('speechSynthesis' in window) {
        speechSynthesis.getVoices(); // Preload voices
    }
});