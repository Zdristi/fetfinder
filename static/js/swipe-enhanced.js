// Enhanced Swipe Functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Enhanced swipe functionality loaded');
    
    let startX = 0;
    let currentX = 0;
    let isDragging = false;
    let currentUserId = null;
    
    // Get the card element
    const card = document.getElementById('currentCard');
    
    if (card) {
        console.log('Setting up enhanced swipe event listeners');
        
        // Setup event listeners for both mouse and touch
        card.addEventListener('pointerdown', startDrag);
        card.addEventListener('mousedown', startDrag);
        card.addEventListener('touchstart', startDrag, { passive: false });
        
        document.addEventListener('pointermove', drag, { passive: false });
        document.addEventListener('mousemove', drag);
        document.addEventListener('touchmove', drag, { passive: false });
        
        document.addEventListener('pointerup', endDrag);
        document.addEventListener('mouseup', endDrag);
        document.addEventListener('touchend', endDrag);
        
        console.log('Enhanced swipe event listeners set up successfully');
    } else {
        console.error('ERROR: Could not find card element with id="currentCard"');
    }
    
    function startDrag(e) {
        console.log('=== ENHANCED START DRAG EVENT ===');
        console.log('Event type:', e.type);
        console.log('Target element:', e.target);
        
        // Prevent default behavior but allow event to propagate
        if (e.type === 'touchstart') {
            startX = e.touches[0].clientX;
            console.log('Touch start at X:', startX);
        } else if (e.type === 'mousedown') {
            startX = e.clientX;
            console.log('Mouse start at X:', startX);
            
            // Prevent text selection during drag
            e.preventDefault();
        } else if (e.type === 'pointerdown') {
            startX = e.clientX;
            console.log('Pointer start at X:', startX);
        }
        
        isDragging = true;
        console.log('=== ENHANCED START DRAG COMPLETED ===');
    }
    
    function drag(e) {
        if (!isDragging) {
            console.log('ENHANCED DRAG: Skipping - not dragging');
            return;
        }
        
        // Prevent default behavior to avoid scrolling/text selection
        e.preventDefault();
        
        let clientX;
        if (e.type === 'touchmove') {
            if (e.touches && e.touches.length > 0) {
                clientX = e.touches[0].clientX;
            } else {
                return;
            }
        } else if (e.type === 'mousemove' || e.type === 'pointermove') {
            clientX = e.clientX;
        } else {
            return;
        }
        
        currentX = clientX - startX;
        
        console.log('ENHANCED DRAG: currentX =', currentX, '(clientX:', clientX, '- startX:', startX, ')');
        
        // Move the card
        const rotation = currentX * 0.1;
        const transformValue = `translateX(${currentX}px) rotate(${rotation}deg)`;
        console.log('ENHANCED DRAG: Setting transform to:', transformValue);
        
        const cardElement = document.getElementById('currentCard');
        console.log('ENHANCED DRAG: Card element:', cardElement);
        
        if (cardElement) {
            // Add dragging class for visual feedback
            cardElement.classList.add('dragging');
            
            // Add transition for smooth movement during drag
            cardElement.style.transition = 'transform 0s cubic-bezier(0.25, 0.1, 0.25, 1)';
            cardElement.style.transform = transformValue;
            console.log('ENHANCED DRAG: Transform actually set to element style');
        } else {
            console.log('ENHANCED DRAG: ERROR - Could not find card element');
        }
        
        // Show action hints based on direction with opacity changes for better visibility
        const absX = Math.abs(currentX);
        const hintOpacity = Math.min(absX / 50, 1); // Opacity increases as card moves further
        
        if (currentX > 50) {
            $('#likeHint').show().css('opacity', hintOpacity);
            $('#dislikeHint').hide();
            console.log('ENHANCED DRAG: Showing LIKE hint with opacity:', hintOpacity);
        } else if (currentX < -50) {
            $('#dislikeHint').show().css('opacity', hintOpacity);
            $('#likeHint').hide();
            console.log('ENHANCED DRAG: Showing DISLIKE hint with opacity:', hintOpacity);
        } else {
            $('#likeHint').hide();
            $('#dislikeHint').hide();
            console.log('ENHANCED DRAG: Hiding both hints');
        }
    }
    
    function endDrag(e) {
        console.log('=== ENHANCED END DRAG EVENT ===');
        console.log('Event type:', e.type);
        
        if (!isDragging) {
            console.log('ENHANCED END DRAG: Skipping - not dragging');
            return;
        }
        
        isDragging = false;
        
        let clientX;
        if (e.type === 'touchend' && e.changedTouches && e.changedTouches.length > 0) {
            clientX = e.changedTouches[0].clientX;
        } else if (e.type === 'mouseup' || e.type === 'pointerup') {
            clientX = e.clientX;
        } else {
            // Fallback to currentX if we can't get clientX
            clientX = currentX + startX;
        }
        
        const diffX = clientX - startX;
        console.log('ENHANCED END DRAG: diffX =', diffX, '(clientX:', clientX, ')');
        
        // Reset transition for smooth animation
        $('#currentCard').css('transition', 'transform 0.3s ease-out, opacity 0.3s ease-out');
        
        if (diffX > 100) {
            console.log('ENHANCED END DRAG: Performing LIKE action');
            // Like action with smooth animation
            $('#currentCard').addClass('swipe-card-liked');
            $('#likeHint').show().fadeOut(200);
            setTimeout(function() {
                // Call the existing swipe function
                if (typeof swipe === 'function') {
                    swipe('like');
                }
            }, 200); // Short delay for animation
        } else if (diffX < -100) {
            console.log('ENHANCED END DRAG: Performing DISLIKE action');
            // Dislike action with smooth animation
            $('#currentCard').addClass('swipe-card-disliked');
            $('#dislikeHint').show().fadeOut(200);
            setTimeout(function() {
                // Call the existing swipe function
                if (typeof swipe === 'function') {
                    swipe('dislike');
                }
            }, 200); // Short delay for animation
        } else {
            console.log('ENHANCED END DRAG: Returning to original position');
            // Return to original position with smooth animation
            $('#currentCard').css({
                'transform': 'translateX(0) rotate(0deg)',
                'transition': 'transform 0.3s cubic-bezier(0.25, 0.1, 0.25, 1), opacity 0.3s cubic-bezier(0.25, 0.1, 0.25, 1)'
            }).removeClass('dragging');
            $('#likeHint').hide();
            $('#dislikeHint').hide();
        }
        
        console.log('=== ENHANCED END DRAG COMPLETED ===');
    }
});