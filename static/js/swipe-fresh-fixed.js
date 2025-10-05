// Fixed Swipe System Implementation
class SwipeSystem {
  constructor() {
    this.users = [];
    this.currentIndex = 0;
    this.isDragging = false;
    this.startX = 0;
    this.startY = 0;
    this.currentX = 0;
    this.currentY = 0;
    this.currentCard = null;
    this.currentUserId = null;
    this.swipeThreshold = 100; // pixels
    this.rotationFactor = 0.1; // rotation factor
    
    this.init();
  }
  
  init() {
    console.log('=== Initializing Fixed Swipe System ===');
    
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.initializeSwipeSystem());
    } else {
      this.initializeSwipeSystem();
    }
  }
  
  initializeSwipeSystem() {
    console.log('=== Initializing Swipe System Components ===');
    
    // Load users
    this.loadUsers();
    
    // Setup event listeners
    this.setupEventListeners();
    
    console.log('=== Swipe System Initialized ===');
  }
  
  loadUsers() {
    console.log('Loading users from API...');
    
    fetch('/api/users')
      .then(response => response.json())
      .then(data => {
        console.log('Users data received:', data);
        
        // Convert to array format
        this.users = data.map(([userId, userData]) => ({
          id: userId,
          ...userData
        }));
        
        console.log('Processed users:', this.users);
        
        if (this.users.length > 0) {
          this.showNextUser();
        } else {
          this.showEmptyState();
        }
      })
      .catch(error => {
        console.error('Error loading users:', error);
        this.showEmptyState(true);
      });
  }
  
  showNextUser() {
    console.log('=== Showing Next User ===');
    console.log('Current index:', this.currentIndex);
    console.log('Total users:', this.users.length);
    
    if (this.currentIndex >= this.users.length) {
      console.log('No more users to show');
      this.showEmptyState();
      return;
    }
    
    const user = this.users[this.currentIndex];
    console.log('Displaying user:', user);
    
    // Update UI with user data
    this.updateUserCard(user);
    
    // Show the card
    const card = document.getElementById('currentCard');
    if (card) {
      card.style.display = 'block';
      // Reset card position and styles
      card.style.transform = 'translateX(0) translateY(0) rotate(0deg)';
      card.style.opacity = '1';
      card.style.transition = 'transform 0.3s cubic-bezier(0.25, 0.1, 0.25, 1), opacity 0.3s cubic-bezier(0.25, 0.1, 0.25, 1)';
      card.classList.remove('swipe-right', 'swipe-left', 'swipe-up');
      console.log('Card displayed');
    }
  }
  
  updateUserCard(user) {
    console.log('Updating card with user data:', user);
    
    // Update user information - only update if elements exist
    const usernameElem = document.getElementById('username');
    if (usernameElem) {
      usernameElem.textContent = user.username || 'Anonymous';
    } else {
      console.error('Username element not found');
    }
    
    // Update location
    const locationElem = document.getElementById('location');
    if (locationElem) {
      if (user.city || user.country) {
        // Add location icon and text
        locationElem.innerHTML = `<i class="fas fa-map-marker-alt location-icon"></i> ${user.city || ''}${user.city && user.country ? ', ' : ''}${user.country || ''}`;
        locationElem.style.display = 'block';
      } else {
        locationElem.style.display = 'none';
      }
    } else {
      console.error('Location element not found');
    }
    
    // Update bio
    const bioElem = document.getElementById('bio');
    if (bioElem) {
      bioElem.textContent = user.bio || 'No bio provided';
    } else {
      console.error('Bio element not found');
    }
    
    // Update avatar
    const avatarElem = document.getElementById('userAvatar');
    if (avatarElem) {
      if (user.photo) {
        // Handle both absolute URLs and relative paths
        let photoUrl;
        if (user.photo.startsWith('http')) {
          photoUrl = user.photo;
        } else if (user.photo.startsWith('/')) {
          photoUrl = user.photo; // Already a complete path
        } else {
          photoUrl = `/static/uploads/${user.photo}`;
        }
        
        // Clear any previous content and styles
        avatarElem.style.backgroundImage = 'none';
        avatarElem.style.background = 'none';
        avatarElem.textContent = '';
        
        // Set background image for the avatar
        avatarElem.style.backgroundImage = `url('${photoUrl}')`;
        avatarElem.style.backgroundSize = 'cover';
        avatarElem.style.backgroundPosition = 'center';
        avatarElem.style.backgroundRepeat = 'no-repeat';
        avatarElem.style.borderRadius = '15px 15px 0 0';
        
        // Add error handling for image loading
        const img = new Image();
        img.onload = function() {
          // Image loaded successfully, make sure it's displayed properly
          avatarElem.style.backgroundImage = `url('${photoUrl}')`;
          avatarElem.style.backgroundSize = 'cover';
          avatarElem.style.backgroundPosition = 'center';
          avatarElem.style.backgroundRepeat = 'no-repeat';
          avatarElem.textContent = ''; // Ensure no text content
        };
        img.onerror = function() {
          // If image fails to load, show gradient with first letter
          avatarElem.style.backgroundImage = 'none';
          avatarElem.textContent = user.username ? user.username.charAt(0).toUpperCase() : '?';
          avatarElem.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
          avatarElem.style.display = 'flex';
          avatarElem.style.alignItems = 'center';
          avatarElem.style.justifyContent = 'center';
          avatarElem.style.fontSize = '4rem';
          avatarElem.style.color = 'white';
          avatarElem.style.borderRadius = '15px 15px 0 0';
        };
        img.src = photoUrl;
      } else {
        // No photo - show gradient with first letter
        avatarElem.style.backgroundImage = 'none';
        avatarElem.textContent = user.username ? user.username.charAt(0).toUpperCase() : '?';
        avatarElem.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
        avatarElem.style.display = 'flex';
        avatarElem.style.alignItems = 'center';
        avatarElem.style.justifyContent = 'center';
        avatarElem.style.fontSize = '4rem';
        avatarElem.style.color = 'white';
      }
    } else {
      console.error('Avatar element not found');
    }
    
    // Update tags
    const tagsContainer = document.getElementById('tags');
    if (tagsContainer) {
      tagsContainer.innerHTML = '';
    
      // Add interests
      if (user.interests && user.interests.length > 0) {
        user.interests.slice(0, 5).forEach(interest => {
          const tag = document.createElement('span');
          tag.className = 'badge badge-interest';
          tag.textContent = interest;
          tagsContainer.appendChild(tag);
        });
      }
    
      // Add fetishes
      if (user.fetishes && user.fetishes.length > 0) {
        user.fetishes.slice(0, 5).forEach(fetish => {
          const tag = document.createElement('span');
          tag.className = 'badge badge-fetish';
          tag.textContent = fetish;
          tagsContainer.appendChild(tag);
        });
      }
    } else {
      console.error('Tags container element not found');
    }
    
    // Store current user ID
    this.currentUserId = user.id;
    console.log('Current user ID set to:', this.currentUserId);
  }
  
  setupEventListeners() {
    console.log('Setting up event listeners...');
    
    const card = document.getElementById('currentCard');
    if (!card) {
      console.error('Could not find currentCard element');
      return;
    }
    
    console.log('Found card element:', card);
    
    // Remove any existing listeners to prevent duplicates
    card.removeEventListener('pointerdown', this.handlePointerDown.bind(this));
    card.removeEventListener('mousedown', this.handleMouseDown.bind(this));
    card.removeEventListener('touchstart', this.handleTouchStart.bind(this));
    
    document.removeEventListener('pointermove', this.handlePointerMove.bind(this));
    document.removeEventListener('mousemove', this.handleMouseMove.bind(this));
    document.removeEventListener('touchmove', this.handleTouchMove.bind(this));
    
    document.removeEventListener('pointerup', this.handlePointerUp.bind(this));
    document.removeEventListener('mouseup', this.handleMouseUp.bind(this));
    document.removeEventListener('touchend', this.handleTouchEnd.bind(this));
    
    // Add new event listeners
    card.addEventListener('pointerdown', this.handlePointerDown.bind(this));
    card.addEventListener('mousedown', this.handleMouseDown.bind(this));
    card.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
    
    // Add document level listeners for smooth dragging
    document.addEventListener('pointermove', this.handlePointerMove.bind(this), { passive: false });
    document.addEventListener('mousemove', this.handleMouseMove.bind(this));
    document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
    
    document.addEventListener('pointerup', this.handlePointerUp.bind(this));
    document.addEventListener('mouseup', this.handleMouseUp.bind(this));
    document.addEventListener('touchend', this.handleTouchEnd.bind(this));
    
    console.log('Event listeners set up successfully');
  }
  
  handlePointerDown(e) {
    console.log('Pointer down event:', e);
    this.startSwipe(e);
  }
  
  handleMouseDown(e) {
    console.log('Mouse down event:', e);
    e.preventDefault(); // Prevent text selection
    this.startSwipe(e);
  }
  
  handleTouchStart(e) {
    console.log('Touch start event:', e);
    if (e.touches.length > 0) {
      this.startSwipe(e.touches[0]);
    }
  }
  
  startSwipe(startEvent) {
    console.log('=== Starting Swipe ===');
    
    const card = document.getElementById('currentCard');
    if (!card) {
      console.log('No card found, skipping swipe start');
      return;
    }
    
    this.isDragging = true;
    this.currentCard = card;
    
    // Get start coordinates
    if (startEvent.clientX !== undefined && startEvent.clientY !== undefined) {
      this.startX = startEvent.clientX;
      this.startY = startEvent.clientY;
    }
    
    console.log('Swipe started at:', this.startX, ',', this.startY);
    
    // Add dragging class for visual feedback
    this.currentCard.classList.add('dragging');
    
    console.log('=== Swipe Started Successfully ===');
  }
  
  handlePointerMove(e) {
    if (this.isDragging) {
      this.moveCard(e);
    }
  }
  
  handleMouseMove(e) {
    if (this.isDragging) {
      this.moveCard(e);
    }
  }
  
  handleTouchMove(e) {
    if (this.isDragging && e.touches.length > 0) {
      e.preventDefault(); // Prevent scrolling
      this.moveCard(e.touches[0]);
    }
  }
  
  moveCard(moveEvent) {
    if (!this.isDragging || !this.currentCard) {
      return;
    }
    
    // Calculate movement
    this.currentX = moveEvent.clientX - this.startX;
    this.currentY = moveEvent.clientY - this.startY;
    
    console.log('Moving card by:', this.currentX, 'x', this.currentY);
    
    // Apply transformation
    const rotation = this.currentX * this.rotationFactor;
    const transform = `translateX(${this.currentX}px) translateY(${this.currentY}px) rotate(${rotation}deg)`;
    
    this.currentCard.style.transform = transform;
    
    // Update opacity based on distance
    const absX = Math.abs(this.currentX);
    const opacity = Math.max(0.7, 1 - absX / 300);
    this.currentCard.style.opacity = opacity;
    
    // Show action hints
    this.showActionHints();
  }
  
  showActionHints() {
    const likeHint = document.getElementById('likeHint');
    const dislikeHint = document.getElementById('dislikeHint');
    
    if (this.currentX > 50) {
      // Show like hint
      if (likeHint) {
        likeHint.classList.add('show');
      }
      if (dislikeHint) {
        dislikeHint.classList.remove('show');
      }
    } else if (this.currentX < -50) {
      // Show dislike hint
      if (dislikeHint) {
        dislikeHint.classList.add('show');
      }
      if (likeHint) {
        likeHint.classList.remove('show');
      }
    } else {
      // Hide both hints
      if (likeHint) {
        likeHint.classList.remove('show');
      }
      if (dislikeHint) {
        dislikeHint.classList.remove('show');
      }
    }
  }
  
  hideActionHints() {
    const likeHint = document.getElementById('likeHint');
    const dislikeHint = document.getElementById('dislikeHint');
    
    if (likeHint) {
      likeHint.classList.remove('show');
    }
    if (dislikeHint) {
      dislikeHint.classList.remove('show');
    }
  }
  
  handlePointerUp(e) {
    if (this.isDragging) {
      this.endSwipe(e);
    }
  }
  
  handleMouseUp(e) {
    if (this.isDragging) {
      this.endSwipe(e);
    }
  }
  
  handleTouchEnd(e) {
    if (this.isDragging) {
      this.endSwipe(e.changedTouches[0]);
    }
  }
  
  endSwipe(endEvent) {
    console.log('=== Ending Swipe ===');
    
    if (!this.isDragging || !this.currentCard) {
      return;
    }
    
    this.isDragging = false;
    
    // Calculate final position
    const finalX = endEvent ? endEvent.clientX - this.startX : this.currentX;
    const finalY = endEvent ? endEvent.clientY - this.startY : this.currentY;
    
    console.log('Final swipe position:', finalX, 'x', finalY);
    
    // Remove dragging class
    this.currentCard.classList.remove('dragging');
    
    // Hide action hints
    this.hideActionHints();
    
    // Check if it's a valid swipe
    if (Math.abs(finalX) > this.swipeThreshold) {
      // It's a horizontal swipe - like or dislike
      const action = finalX > 0 ? 'like' : 'dislike';
      console.log('Performing', action, 'action');
      this.performSwipe(action);
    } else if (finalY < -this.swipeThreshold) {
      // It's a vertical swipe up - superlike
      console.log('Performing superlike action');
      this.performSwipe('superlike');
    } else {
      // Return to center
      console.log('Returning card to center');
      this.returnToCenter();
    }
    
    console.log('=== Swipe Ended ===');
  }
  
  returnToCenter() {
    if (!this.currentCard) return;
    
    // Add transition for smooth return
    this.currentCard.style.transition = 'transform 0.3s cubic-bezier(0.25, 0.1, 0.25, 1), opacity 0.3s cubic-bezier(0.25, 0.1, 0.25, 1)';
    this.currentCard.style.transform = 'translateX(0) translateY(0) rotate(0deg)';
    this.currentCard.style.opacity = '1';
    
    // Clean up transition after animation
    setTimeout(() => {
      if (this.currentCard) {
        this.currentCard.style.transition = '';
      }
    }, 300);
  }
  
  performSwipe(action) {
    if (!this.currentCard || !this.currentUserId) {
      console.log('Cannot perform swipe - no card or user ID');
      return;
    }
    
    console.log('Performing swipe action:', action, 'for user:', this.currentUserId);
    
    // Add swipe animation class
    if (action === 'like') {
      this.currentCard.classList.add('swipe-right');
    } else if (action === 'dislike') {
      this.currentCard.classList.add('swipe-left');
    } else if (action === 'superlike') {
      this.currentCard.classList.add('swipe-up');
    }
    
    // Send swipe data to server
    fetch('/api/match', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user2: this.currentUserId,
        action: action
      })
    })
    .then(response => response.json())
    .then(data => {
      console.log('Swipe processed, response:', data);
      
      // Check for match notification
      if (data.mutual_match) {
        this.showMatchNotification(data.matched_user_name, data.matched_user_photo);
      }
    })
    .catch(error => {
      console.error('Error processing swipe:', error);
    });
    
    // Show next user after animation
    setTimeout(() => {
      // Don't remove the card, just hide it and show the next user
      if (this.currentCard) {
        this.currentCard.style.transition = 'transform 0.4s ease, opacity 0.4s ease';
        // Move the card out of view based on swipe direction
        if (action === 'like') {
          this.currentCard.style.transform = 'translateX(150vw) rotate(20deg)';
        } else if (action === 'dislike') {
          this.currentCard.style.transform = 'translateX(-150vw) rotate(-20deg)';
        } else if (action === 'superlike') {
          this.currentCard.style.transform = 'translateY(-150vh) rotate(0deg)';
        }
        this.currentCard.style.opacity = '0';
      }
      
      // Move to next user
      this.currentIndex++;
      // Add a small delay to ensure animation completes
      setTimeout(() => {
        this.showNextUser();
      }, 200);
    }, 300);
  }
  
  showMatchNotification(userName, userPhoto) {
    console.log('Showing match notification for:', userName);
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'match-notification';
    notification.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: rgba(255,255,255,0.95);
      padding: 20px;
      border-radius: 15px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      z-index: 10000;
      text-align: center;
      display: none;
    `;
    
    // Use translations if available, otherwise fallback to English
    const continueSwipingText = typeof translations !== 'undefined' ? translations['continue_swiping'] : 'Continue Swiping';
    const viewMatchesText = typeof translations !== 'undefined' ? translations['view_matches'] : 'View Matches';
    
    notification.innerHTML = `
      <div style="font-size: 3rem;">❤️</div>
      <h3 style="color: #28a745; margin: 10px 0;">It's a Match!</h3>
      <p style="margin: 0;">You and ${userName || 'someone'} liked each other</p>
      <div style="margin-top: 15px; display: flex; justify-content: center; gap: 10px; flex-wrap: wrap;">
        <button class="btn btn-primary" onclick="this.closest('.match-notification').remove()">${continueSwipingText}</button>
        <a href="/matches" class="btn btn-primary">${viewMatchesText}</a>
      </div>
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Show with fade in
    setTimeout(() => {
      notification.style.display = 'block';
      notification.style.opacity = '0';
      notification.style.transition = 'opacity 0.3s ease';
      setTimeout(() => {
        notification.style.opacity = '1';
      }, 10);
    }, 10);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.style.opacity = '0';
        setTimeout(() => {
          if (notification.parentNode) {
            notification.remove();
          }
        }, 300);
      }
    }, 5000);
  }
  
  showEmptyState(isError = false) {
    console.log('Showing empty state, isError:', isError);
    
    // Hide the swipe area
    const swipeArea = document.getElementById('swipeArea');
    if (swipeArea) {
      swipeArea.style.display = 'none';
    }
    
    // Show the existing no users message
    const noUsersMessage = document.getElementById('noUsersMessage');
    if (noUsersMessage) {
      noUsersMessage.style.display = 'block';
    } else {
      // Fallback: create and display the message if element doesn't exist
      const container = document.querySelector('.swipe-container');
      if (container) {
        if (isError) {
          container.innerHTML = `
            <div class="empty-state">
              <div>⚠️</div>
              <h3>Error loading users</h3>
              <p>Please try again later</p>
          </div>
        `;
        } else {
          container.innerHTML = `
            <div class="empty-state">
              <div>👥</div>
              <h3>No more users to show</h3>
              <p>Check back later for new matches!</p>
          </div>
        `;
        }
      }
    }
  }
}

// Initialize the swipe system when the page loads
document.addEventListener('DOMContentLoaded', function() {
  console.log('=== DOM Loaded - Initializing Swipe System ===');
  window.swipeSystem = new SwipeSystem();
});

// Global function for button clicks
function swipe(action) {
  console.log('Swipe action triggered by button:', action);
  
  // Visual feedback on button click
  const button = event ? event.currentTarget : null;
  if (button) {
    button.style.transform = 'scale(0.9)';
    setTimeout(() => {
      button.style.transform = '';
    }, 100);
  }
  
  // Perform the swipe if we have a current user
  if (window.swipeSystem && window.swipeSystem.currentUserId) {
    window.swipeSystem.performSwipe(action);
  } else {
    console.log('No current user to swipe on');
  }
}

// Superlike function
function superlike() {
  swipe('superlike');
}

// Undo swipe function
function undoSwipe() {
  console.log('Undo swipe requested');
  // In a real implementation, this would connect to backend
  alert('Undo swipe is a premium feature! Upgrade to premium to use this feature.');
}

// Message modal functions
function openMessageModal() {
  console.log('Opening message modal');
  const modal = document.getElementById('messageModal');
  if (modal) {
    modal.style.display = 'flex';
  }
}

function closeMessageModal() {
  console.log('Closing message modal');
  const modal = document.getElementById('messageModal');
  if (modal) {
    modal.style.display = 'none';
  }
}

function sendMessageInsteadOfLike() {
  console.log('Sending message instead of like');
  
  const messageInput = document.getElementById('messageInput');
  const messageContent = messageInput.value.trim();
  
  if (!messageContent) {
    alert('Please enter a message');
    return;
  }
  
  // In a real implementation, this would send the message to backend
  alert('Message sent successfully!');
  closeMessageModal();
  
  // Also perform like action
  swipe('like');
}