// Enhanced Swipe Functionality with Improved Drag Handling
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== ENHANCED SWIPE FUNCTIONALITY INITIALIZED ===');
    
    // State variables
    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let currentY = 0;
    let isDragging = false;
    let currentCard = null;
    let currentUserId = null;
    
    // Initialize drag events when DOM is loaded
    initDragEvents();
    
    function initDragEvents() {
        console.log('=== INITIALIZING DRAG EVENTS ===');
        
        // Get the current card element by ID (as in the template)
        const card = document.getElementById('currentCard');
        if (!card) {
            console.error('Could not find card element with id="currentCard"');
            return;
        }
        
        console.log('Card element found:', card);
        
        // Remove any existing event listeners to prevent duplicates
        card.removeEventListener('pointerdown', startDrag);
        card.removeEventListener('mousedown', startDrag);
        card.removeEventListener('touchstart', startDrag);
        
        // Add enhanced event listeners
        card.addEventListener('pointerdown', startDrag);
        card.addEventListener('mousedown', startDrag);
        card.addEventListener('touchstart', startDrag, { passive: false });
        
        // Add document-level listeners for smoother dragging
        document.removeEventListener('pointermove', duringDrag);
        document.removeEventListener('mousemove', duringDrag);
        document.removeEventListener('touchmove', duringDrag);
        
        document.removeEventListener('pointerup', endDrag);
        document.removeEventListener('mouseup', endDrag);
        document.removeEventListener('touchend', endDrag);
        
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
        
        // Only handle drag on the current card
        const card = document.getElementById('currentCard');
        if (!card) {
            console.log('START DRAG: Card not found, ignoring');
            return;
        }
        
        isDragging = true;
        currentCard = card;
        currentUserId = currentUserId; // This should come from the template context
        
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
        if (!isDragging || !currentCard) {
            console.log('DRAG: Skipping - not dragging or no current card');
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
        const likeHint = document.getElementById('likeHint');
        const dislikeHint = document.getElementById('dislikeHint');
        
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
        
        if (!isDragging || !currentCard) {
            console.log('END DRAG: Skipping - not dragging or no current card');
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
            const likeHint = document.getElementById('likeHint');
            const dislikeHint = document.getElementById('dislikeHint');
            if (likeHint) likeHint.style.display = 'none';
            if (dislikeHint) dislikeHint.style.display = 'none';
            
            // Perform the swipe action after a short delay for animation
            setTimeout(() => {
                if (typeof swipe === 'function') {
                    swipe(action);
                }
            }, 200);
        } else {
            // Return to center
            console.log('END DRAG: Returning to original position');
            currentCard.style.transform = 'translateX(0) translateY(0) rotate(0deg)';
            currentCard.style.opacity = '1';
            
            // Remove dragging class
            currentCard.classList.remove('dragging');
            
            // Hide hints
            const likeHint = document.getElementById('likeHint');
            const dislikeHint = document.getElementById('dislikeHint');
            if (likeHint) likeHint.style.display = 'none';
            if (dislikeHint) dislikeHint.style.display = 'none';
        }
        
        console.log('=== END DRAG COMPLETED ===');
    }
});