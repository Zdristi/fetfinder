// Swipe functionality
document.addEventListener('DOMContentLoaded', function() {
    initSwipe();
});

function initSwipe() {
    let users = [];
    let currentIndex = 0;
    let startX, startY, moveX, moveY;
    let currentCard = null;
    
    // Fetch users
    fetch('/api/users')
        .then(response => response.json())
        .then(data => {
            // Convert object entries to array of users
            users = data.map(([userId, userData]) => ({
                id: userId,
                ...userData
            }));
            
            if (users.length > 0) {
                renderCards();
                initTouchEvents();
                initKeyboardEvents();
            } else {
                document.querySelector('.card-stack').innerHTML = `
                    <div class="empty-state">
                        <div>👥</div>
                        <h3>${getTranslatedText('no_more_users')}</h3>
                        <p>${getTranslatedText('check_later')}</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error fetching users:', error);
            document.querySelector('.card-stack').innerHTML = `
                <div class="empty-state">
                    <div>⚠️</div>
                    <h3>Error loading users</h3>
                    <p>Please try again later</p>
                </div>
            `;
        });
    
    function renderCards() {
        const stack = document.querySelector('.card-stack');
        stack.innerHTML = '';
        
        // Show up to 3 cards
        for (let i = 0; i < Math.min(3, users.length - currentIndex); i++) {
            const userIndex = currentIndex + i;
            if (userIndex >= users.length) break;
            
            const user = users[userIndex];
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
    }
    
    function initTouchEvents() {
        const topCard = document.querySelector('.swipe-card.top');
        if (!topCard) return;
        
        // Mouse events
        topCard.addEventListener('mousedown', startDrag);
        document.addEventListener('mousemove', duringDrag);
        document.addEventListener('mouseup', endDrag);
        
        // Touch events
        topCard.addEventListener('touchstart', handleTouchStart);
        document.addEventListener('touchmove', handleTouchMove);
        document.addEventListener('touchend', handleTouchEnd);
    }
    
    function initKeyboardEvents() {
        document.addEventListener('keydown', function(e) {
            // Only handle if we have cards
            if (users.length <= currentIndex) return;
            
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    animateSwipe('dislike');
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    animateSwipe('like');
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    animateSwipe('superlike');
                    break;
            }
        });
    }
    
    function handleTouchStart(e) {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        currentCard = document.querySelector('.swipe-card.top');
    }
    
    function handleTouchMove(e) {
        if (!currentCard) return;
        
        moveX = e.touches[0].clientX;
        moveY = e.touches[0].clientY;
        
        const diffX = moveX - startX;
        const diffY = moveY - startY;
        
        // Update card position
        currentCard.style.transform = `translate(${diffX}px, ${diffY}px) rotate(${diffX * 0.1}deg)`;
        
        // Update opacity based on distance
        const opacity = 1 - Math.abs(diffX) / 300;
        currentCard.style.opacity = Math.max(0.7, opacity);
    }
    
    function handleTouchEnd(e) {
        if (!currentCard) return;
        
        const diffX = moveX - startX;
        const diffY = moveY - startY;
        
        // Determine swipe direction
        if (Math.abs(diffX) > 100) {
            // Swipe left or right
            const action = diffX > 0 ? 'like' : 'dislike';
            animateSwipe(action);
        } else if (Math.abs(diffY) > 100 && diffY < 0) {
            // Swipe up for superlike
            animateSwipe('superlike');
        } else {
            // Return to center
            currentCard.style.transition = 'transform 0.3s, opacity 0.3s';
            currentCard.style.transform = 'translate(0, 0) rotate(0deg)';
            currentCard.style.opacity = '1';
            
            setTimeout(() => {
                currentCard.style.transition = '';
            }, 300);
        }
        
        currentCard = null;
    }
    
    function startDrag(e) {
        startX = e.clientX;
        startY = e.clientY;
        currentCard = document.querySelector('.swipe-card.top');
    }
    
    function duringDrag(e) {
        if (!currentCard) return;
        
        moveX = e.clientX;
        moveY = e.clientY;
        
        const diffX = moveX - startX;
        const diffY = moveY - startY;
        
        // Update card position
        currentCard.style.transform = `translate(${diffX}px, ${diffY}px) rotate(${diffX * 0.1}deg)`;
        
        // Update opacity based on distance
        const opacity = 1 - Math.abs(diffX) / 300;
        currentCard.style.opacity = Math.max(0.7, opacity);
    }
    
    function endDrag(e) {
        if (!currentCard) return;
        
        moveX = e.clientX;
        moveY = e.clientY;
        
        const diffX = moveX - startX;
        const diffY = moveY - startY;
        
        // Determine swipe direction
        if (Math.abs(diffX) > 100) {
            // Swipe left or right
            const action = diffX > 0 ? 'like' : 'dislike';
            animateSwipe(action);
        } else if (Math.abs(diffY) > 100 && diffY < 0) {
            // Swipe up for superlike
            animateSwipe('superlike');
        } else {
            // Return to center
            currentCard.style.transition = 'transform 0.3s, opacity 0.3s';
            currentCard.style.transform = 'translate(0, 0) rotate(0deg)';
            currentCard.style.opacity = '1';
            
            setTimeout(() => {
                currentCard.style.transition = '';
            }, 300);
        }
        
        currentCard = null;
    }
    
    function animateSwipe(action) {
        if (currentIndex >= users.length) return;
        
        const user = users[currentIndex];
        const card = document.querySelector('.swipe-card.top');
        
        if (!card) return;
        
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
        
        // Animate card
        card.style.transition = 'transform 0.3s, opacity 0.3s';
        
        if (action === 'like') {
            card.style.transform = 'translate(100vw, 0) rotate(30deg)';
            card.style.opacity = '0';
        } else if (action === 'dislike') {
            card.style.transform = 'translate(-100vw, 0) rotate(-30deg)';
            card.style.opacity = '0';
        } else if (action === 'superlike') {
            card.style.transform = 'translate(0, -100vh) rotate(0deg)';
            card.style.opacity = '0';
        }
        
        setTimeout(() => {
            currentIndex++;
            if (currentIndex < users.length) {
                renderCards();
                initTouchEvents();
            } else {
                document.querySelector('.card-stack').innerHTML = `
                    <div class="empty-state">
                        <div>👥</div>
                        <h3>${getTranslatedText('no_more_users')}</h3>
                        <p>${getTranslatedText('check_later')}</p>
                    </div>
                `;
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
        
        animateSwipe(action);
    };
}

// Simple translation function for swipe page
function getTranslatedText(key) {
    // This is a simplified version - in a real app, you'd get this from the server
    const translations = {
        'no_more_users': document.documentElement.lang === 'ru' ? 'Больше нет пользователей для показа' : 'No more users to show',
        'check_later': document.documentElement.lang === 'ru' ? 'Загляните позже для новых совпадений!' : 'Check back later for new matches!'
    };
    return translations[key] || key;
}