// Enhanced Swipe Functionality with Improved Drag Handling
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== ENHANCED SWIPE FUNCTIONALITY INITIALIZED ===');
    
    // State variables
    let users = [];
    let currentIndex = 0;
    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let currentY = 0;
    let isDragging = false;
    let currentCard = null;
    let currentUserId = null;
    
    // Fetch users when page loads
    fetch('/api/users')
        .then(response => response.json())
        .then(data => {
            console.log('=== USERS DATA RECEIVED ===');
            console.log('Raw data:', data);
            
            // Convert object entries to array of users
            users = data.map(([userId, userData]) => ({
                id: userId,
                ...userData
            }));
            
            console.log('Processed users array:', users);
            
            if (users.length > 0) {
                renderCards();
                initDragEvents();
            } else {
                showEmptyState();
            }
        })
        .catch(error => {
            console.error('Error fetching users:', error);
            showEmptyState(true);
        });
    
    function showEmptyState(isError = false) {
        const stack = document.querySelector('.card-stack');
        if (stack) {
            if (isError) {
                stack.innerHTML = `
                    <div class="empty-state">
                        <div>⚠️</div>
                        <h3>Error loading users</h3>
                        <p>Please try again later</p>
                    </div>
                `;
            } else {
                stack.innerHTML = `
                    <div class="empty-state">
                        <div>👥</div>
                        <h3>No more users to show</h3>
                        <p>Check back later for new matches!</p>
                    </div>
                `;
            }
        }
    }
    
    function renderCards() {
        console.log('=== RENDERING CARDS ===');
        console.log('Current index:', currentIndex);
        console.log('Users array length:', users.length);
        
        const stack = document.querySelector('.card-stack');
        if (!stack) {
            console.error('Could not find card stack element');
            return;
        }
        
        stack.innerHTML = '';
        
        // Show up to 3 cards for stack effect
        for (let i = 0; i < Math.min(3, users.length - currentIndex); i++) {
            const userIndex = currentIndex + i;
            if (userIndex >= users.length) break;
            
            const user = users[userIndex];
            console.log(`Rendering card ${i} for user:`, user);
            
            const card = document.createElement('div');
            card.className = `swipe-card ${i === 0 ? 'top' : i === 1 ? 'middle' : 'bottom'}`;
            card.dataset.userId = user.id;
            
            // Determine avatar content
            let avatarContent = user.username ? user.username.charAt(0).toUpperCase() : '?';
            let avatarStyle = '';
            
            if (user.photo) {
                const photoUrl = user.photo.startsWith('http') ? 
                    user.photo : 
                    `/static/uploads/${user.photo}`;
                avatarContent = '';
                avatarStyle = `background-image: url('${photoUrl}'); background-size: cover;`;
                console.log('Using photo URL:', photoUrl);
            }
            
            // Location info
            let locationInfo = '';
            if (user.city || user.country) {
                locationInfo = `
                    <p style="margin: 5px 0; color: var(--gray);">
                        <i class="fas fa-map-marker-alt"></i> 
                        ${user.city || ''}${user.city && user.country ? ', ' : ''}${user.country || ''}
                    </p>
                `;
            }
            
            card.innerHTML = `
                <div class="card-image" style="${avatarStyle}">
                    ${avatarContent}
                </div>
                <div class="card-content">
                    <h2>${user.username || 'Anonymous'}</h2>
                    ${locationInfo}
                    <p>${user.bio || 'No bio provided'}</p>
                    
                    ${user.interests && user.interests.length > 0 ? `
                    <div>
                        <strong>Interests:</strong>
                        <div class="card-tags">
                            ${user.interests.slice(0, 5).map(interest => 
                                `<span class="badge badge-interest">${interest}</span>`
                            ).join('')}
                        </div>
                    </div>` : ''}
                    
                    ${user.fetishes && user.fetishes.length > 0 ? `
                    <div>
                        <strong>Fetishes:</strong>
                        <div class="card-tags">
                            ${user.fetishes.slice(0, 5).map(fetish => 
                                `<span class="badge badge-fetish">${fetish}</span>`
                            ).join('')}
                        </div>
                    </div>` : ''}
                </div>
                
                <!-- Action hints -->
                <div class="action-hint like-hint">
                    <i class="fas fa-heart"></i> LIKE
                </div>
                <div class="action-hint dislike-hint">
                    <i class="fas fa-times"></i> NOPE
                </div>
                
                <!-- Swipe buttons overlay -->
                <div style="position: absolute; bottom: 20px; left: 0; right: 0; display: flex; justify-content: center; gap: 20px; pointer-events: none;">
                    <button class="action-btn reject-btn" style="pointer-events: auto;" onclick="swipeAction('dislike', this)">
                        <i class="fas fa-times"></i>
                    </button>
                    <button class="action-btn superlike-btn" style="pointer-events: auto;" onclick="swipeAction('superlike', this)">
                        <i class="fas fa-star"></i>
                    </button>
                    <button class="action-btn like-btn" style="pointer-events: auto;" onclick="swipeAction('like', this)">
                        <i class="fas fa-heart"></i>
                    </button>
                </div>
            `;
            
            stack.appendChild(card);
        }
        
        console.log('=== CARDS RENDERED SUCCESSFULLY ===');
    }
    
    function initDragEvents() {
        console.log('=== INITIALIZING DRAG EVENTS ===');
        
        const topCard = document.querySelector('.swipe-card.top');
        if (!topCard) {
            console.error('Could not find top card for drag events');
            return;
        }
        
        console.log('Top card found:', topCard);
        
        // Remove any existing event listeners to prevent duplicates
        topCard.removeEventListener('pointerdown', startDrag);
        topCard.removeEventListener('mousedown', startDrag);
        topCard.removeEventListener('touchstart', startDrag);
        
        topCard.removeEventListener('pointermove', duringDrag);
        topCard.removeEventListener('mousemove', duringDrag);
        topCard.removeEventListener('touchmove', duringDrag);
        
        topCard.removeEventListener('pointerup', endDrag);
        topCard.removeEventListener('mouseup', endDrag);
        topCard.removeEventListener('touchend', endDrag);
        
        // Add enhanced event listeners
        topCard.addEventListener('pointerdown', startDrag);
        topCard.addEventListener('mousedown', startDrag);
        topCard.addEventListener('touchstart', startDrag, { passive: false });
        
        // Add document-level listeners for smoother dragging
        document.addEventListener('pointermove', duringDrag, { passive: false });
        document.addEventListener('mousemove', duringDrag);
        document.addEventListener('touchmove', duringDrag, { passive: false });
        
        document.addEventListener('pointerup', endDrag);
        document.addEventListener('mouseup', endDrag);
        document.addEventListener('touchend', endDrag);
        
        console.log('=== DRAG EVENTS INITIALIZED SUCCESSFULLY ===');
    }
    
    function startDrag(e) {
        console.log('=== START DRAG EVENT ===');
        console.log('Event type:', e.type);
        console.log('Target element:', e.target);
        
        // Only handle drag on the top card
        const topCard = document.querySelector('.swipe-card.top');
        if (!topCard || (e.target !== topCard && !topCard.contains(e.target))) {
            console.log('START DRAG: Not on top card, ignoring');
            return;
        }
        
        isDragging = true;
        currentCard = topCard;
        currentUserId = currentCard.dataset.userId;
        
        if (e.type === 'touchstart') {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            console.log('Touch start at X:', startX, 'Y:', startY);
        } else {
            startX = e.clientX;
            startY = e.clientY;
            console.log('Mouse/Pointer start at X:', startX, 'Y:', startY);
            
            // Prevent text selection during drag
            if (e.type === 'mousedown') {
                e.preventDefault();
            }
        }
        
        // Add visual feedback class
        currentCard.classList.add('dragging');
        
        console.log('=== START DRAG COMPLETED ===');
    }
    
    function duringDrag(e) {
        if (!isDragging || !currentCard || !currentUserId) {
            console.log('DRAG: Skipping - not dragging or no current user');
            return;
        }
        
        e.preventDefault(); // Prevent scrolling while dragging
        
        let clientX, clientY;
        if (e.type === 'touchmove') {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else {
            clientX = e.clientX;
            clientY = e.clientY;
        }
        
        currentX = clientX - startX;
        currentY = clientY - startY;
        
        console.log('DRAG: currentX =', currentX, '(clientX:', clientX, '- startX:', startX, ')');
        console.log('DRAG: currentY =', currentY, '(clientY:', clientY, '- startY:', startY, ')');
        
        // Update card position with rotation based on horizontal movement
        const rotation = currentX * 0.1;
        const transformValue = `translateX(${currentX}px) translateY(${currentY}px) rotate(${rotation}deg)`;
        console.log('DRAG: Setting transform to:', transformValue);
        
        // Apply transform without transition for smooth dragging
        currentCard.style.transition = 'none';
        currentCard.style.transform = transformValue;
        
        // Update opacity based on distance for visual feedback
        const absX = Math.abs(currentX);
        const opacity = Math.max(0.7, 1 - absX / 300);
        currentCard.style.opacity = opacity;
        
        // Show action hints based on direction
        const likeHint = currentCard.querySelector('.like-hint');
        const dislikeHint = currentCard.querySelector('.dislike-hint');
        
        if (likeHint && dislikeHint) {
            if (currentX > 50) {
                likeHint.style.display = 'block';
                dislikeHint.style.display = 'none';
                console.log('DRAG: Showing LIKE hint');
            } else if (currentX < -50) {
                dislikeHint.style.display = 'block';
                likeHint.style.display = 'none';
                console.log('DRAG: Showing DISLIKE hint');
            } else {
                likeHint.style.display = 'none';
                dislikeHint.style.display = 'none';
                console.log('DRAG: Hiding both hints');
            }
        }
    }
    
    function endDrag(e) {
        console.log('=== END DRAG EVENT ===');
        console.log('Event type:', e.type);
        
        if (!isDragging || !currentCard || !currentUserId) {
            console.log('END DRAG: Skipping - not dragging or no current user');
            return;
        }
        
        isDragging = false;
        
        let clientX, clientY;
        if (e.type === 'touchend' && e.changedTouches.length > 0) {
            clientX = e.changedTouches[0].clientX;
            clientY = e.changedTouches[0].clientY;
        } else if (e.type === 'mouseup' || e.type === 'pointerup') {
            clientX = e.clientX;
            clientY = e.clientY;
        }
        
        const diffX = (clientX || (currentX + startX)) - startX;
        const diffY = (clientY || (currentY + startY)) - startY;
        
        console.log('END DRAG: diffX =', diffX, '(clientX:', clientX, ')');
        console.log('END DRAG: diffY =', diffY, '(clientY:', clientY, ')');
        
        // Reset transition for smooth animation
        currentCard.style.transition = 'transform 0.3s ease-out, opacity 0.3s ease-out';
        
        // Determine swipe direction
        if (Math.abs(diffX) > 100) {
            // Horizontal swipe - like or dislike
            const action = diffX > 0 ? 'like' : 'dislike';
            console.log('END DRAG: Performing', action.toUpperCase(), 'action');
            
            // Add animation classes
            if (action === 'like') {
                currentCard.classList.add('swipe-card-liked');
            } else {
                currentCard.classList.add('swipe-card-disliked');
            }
            
            // Hide hints
            const likeHint = currentCard.querySelector('.like-hint');
            const dislikeHint = currentCard.querySelector('.dislike-hint');
            if (likeHint) likeHint.style.display = 'none';
            if (dislikeHint) dislikeHint.style.display = 'none';
            
            // Perform the swipe action after a short delay for animation
            setTimeout(() => {
                performSwipe(action);
            }, 200);
        } else if (Math.abs(diffY) > 100 && diffY < 0) {
            // Vertical swipe up - superlike
            console.log('END DRAG: Performing SUPERLIKE action');
            currentCard.classList.add('swipe-card-superliked');
            
            // Hide hints
            const likeHint = currentCard.querySelector('.like-hint');
            const dislikeHint = currentCard.querySelector('.dislike-hint');
            if (likeHint) likeHint.style.display = 'none';
            if (dislikeHint) dislikeHint.style.display = 'none';
            
            // Perform the swipe action after a short delay for animation
            setTimeout(() => {
                performSwipe('superlike');
            }, 200);
        } else {
            // Return to center
            console.log('END DRAG: Returning to original position');
            currentCard.style.transform = 'translateX(0) translateY(0) rotate(0deg)';
            currentCard.style.opacity = '1';
            
            // Remove dragging class
            currentCard.classList.remove('dragging');
            
            // Hide hints
            const likeHint = currentCard.querySelector('.like-hint');
            const dislikeHint = currentCard.querySelector('.dislike-hint');
            if (likeHint) likeHint.style.display = 'none';
            if (dislikeHint) dislikeHint.style.display = 'none';
        }
        
        console.log('=== END DRAG COMPLETED ===');
    }
    
    function performSwipe(action) {
        if (currentIndex >= users.length) {
            console.log('No more users to swipe');
            return;
        }
        
        const user = users[currentIndex];
        const card = document.querySelector('.swipe-card.top');
        
        if (!card) {
            console.log('No card to perform swipe on');
            return;
        }
        
        console.log('Performing', action, 'for user:', user);
        
        // Send match data to server
        fetch('/api/match', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user2: user.id,
                action: action
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Match response:', data);
            
            // Show match notification if it's a mutual match
            if (data.mutual_match) {
                console.log('Showing match notification for:', data.matched_user_name);
                showMatchNotification(data.matched_user_name, data.matched_user_photo);
            }
        })
        .catch(error => {
            console.error('Error sending match:', error);
        });
        
        // Remove the swiped card after animation
        setTimeout(() => {
            card.remove();
            currentIndex++;
            
            if (currentIndex < users.length) {
                // Render next card if available
                renderCards();
                initDragEvents();
            } else {
                // Show empty state when no more users
                showEmptyState();
            }
        }, 300);
    }
    
    // Show match notification
    function showMatchNotification(userName, userPhoto) {
        console.log('Creating match notification for:', userName);
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'match-notification';
        notification.innerHTML = `
            <div class="match-content">
                <div class="match-icon">❤️</div>
                <h3>It's a Match!</h3>
                <p>You and ${userName} liked each other</p>
                <div class="match-actions">
                    <button class="btn btn-outline" onclick="closeNotification(this)">Continue Swiping</button>
                    <a href="/matches" class="btn">View Matches</a>
                </div>
            </div>
        `;
        
        // Add to body
        document.body.appendChild(notification);
        console.log('Notification added to DOM');
        
        // Auto close after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
                console.log('Notification removed');
            }
        }, 5000);
    }
    
    // Close notification
    window.closeNotification = function(button) {
        const notification = button.closest('.match-notification');
        if (notification) {
            notification.remove();
        }
    };
    
    // Make swipeAction available globally
    window.swipeAction = function(action, button) {
        // Add visual feedback
        if (button) {
            button.style.transform = 'scale(0.9)';
            setTimeout(() => {
                button.style.transform = '';
            }, 100);
        }
        
        // Perform the swipe action
        performSwipe(action);
    };
    
    // Keyboard controls for accessibility
    document.addEventListener('keydown', function(e) {
        // Only handle if we have cards
        if (users.length <= currentIndex) return;
        
        switch(e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                performSwipe('dislike');
                break;
            case 'ArrowRight':
                e.preventDefault();
                performSwipe('like');
                break;
            case 'ArrowUp':
                e.preventDefault();
                performSwipe('superlike');
                break;
        }
    });
});

// Simple translation function for swipe page
function getTranslatedText(key) {
    // This is a simplified version - in a real app, you'd get this from the server
    const translations = {
        'no_more_users': document.documentElement.lang === 'ru' ? 'Больше нет пользователей для показа' : 'No more users to show',
        'check_later': document.documentElement.lang === 'ru' ? 'Загляните позже для новых совпадений!' : 'Check back later for new matches!'
    };
    return translations[key] || key;
}