    function showNextUser() {
        console.log('=== showNextUser called ===');
        console.log('Current index:', currentIndex);
        console.log('Total users in array:', users ? users.length : 'null');
        console.log('Users array:', users);
        
        // Reset card completely before showing new user
        if (typeof resetCard === 'function') {
            resetCard();
        }
        
        if (!users || users.length === 0) {
            console.log('Users array is empty or null, calling loadNextUser');
            loadNextUser();
            return;
        }
        
        if (currentIndex >= users.length) {
            // Try to load more users
            console.log('Current index exceeds array length, loading next user from API');
            loadNextUser();
            return;
        }

        const userData = users[currentIndex];
        console.log('User data structure:', userData);
        
        // Check if data structure is correct
        if (!userData || userData.length < 2) {
            console.error('Invalid user data structure:', userData);
            currentIndex++;
            showNextUser(); // Try next user
            return;
        }
        
        const user = userData[1];
        currentUserId = userData[0];
        
        console.log('Displaying user:', user);
        console.log('Setting currentUserId to:', currentUserId);
        
        $('#username').text(user.username || 'Anonymous');
        $('#location').text((user.city || '') + (user.city && user.country ? ', ' : '') + (user.country || ''));
        $('#bio').text(user.bio || 'No bio provided');
        
        // Set avatar with error handling
        const avatarDiv = $('#userAvatar');
        avatarDiv.removeClass('error-loading'); // Remove any previous error classes
        
        if (user.photo) {
            if (user.photo.startsWith('http')) {
                avatarDiv.css('background-image', 'url("' + user.photo + '")');
            } else {
                const photoUrl = "/static/uploads/" + user.photo;
                console.log('Loading photo from:', photoUrl);
                avatarDiv.css('background-image', 'url("' + photoUrl + '")')
                         .on('error', function() {
                            console.error('Failed to load photo:', photoUrl);
                            $(this).addClass('error-loading');
                         });
            }
        } else {
            avatarDiv.css('background-image', 'none');
            avatarDiv.css('background', 'linear-gradient(135deg, #667eea, #764ba2)');
            avatarDiv.text((user.username || '?')[0].toUpperCase());
        }
        
        // Set tags
        const tagsContainer = $('#tags');
        tagsContainer.empty();
        
        if (user.fetishes && user.fetishes.length > 0) {
            user.fetishes.slice(0, 5).forEach(function(fetish) { // Show max 5 fetishes
                tagsContainer.append('<span class="badge badge-fetish">' + fetish + '</span>');
            });
        }
        
        if (user.interests && user.interests.length > 0) {
            user.interests.slice(0, 5).forEach(function(interest) { // Show max 5 interests
                tagsContainer.append('<span class="badge badge-interest">' + interest + '</span>');
            });
        }
        
        console.log('Displaying user card for user ID:', currentUserId);
        
        // Completely reset card animations and styles with smooth transition
        $('#currentCard').removeClass('swipe-card-liked swipe-card-disliked')
                        .removeAttr('style') // Remove all inline styles
                        .css({
                            'transform': 'translateX(0) rotate(0deg)',
                            'transition': 'all 0.3s ease',
                            'display': 'block',
                            'opacity': '1',
                            'position': 'relative',
                            'margin': '20px auto',
                            'max-width': '400px'
                        })
                        .show();
        
        // Reset avatar specifically
        $('#userAvatar').removeAttr('style')
                        .css({
                            'width': '100%',
                            'height': '300px',
                            'background-size': 'cover',
                            'background-position': 'center',
                            'border-radius': '10px 10px 0 0'
                        });
        
        // Reset user info container
        $('.user-info').removeAttr('style')
                      .css({
                          'padding': '20px'
                      });
        
        // Force reflow
        $('#currentCard')[0].offsetHeight;
        
        // Apply final styles
        $('#currentCard').css({
            'transform': 'translateX(0) rotate(0deg)',
            'transition': 'all 0.3s ease',
            'display': 'block',
            'opacity': '1'
        });
        
        // Hide action hints
        $('#likeHint').hide();
        $('#dislikeHint').hide();
        
        console.log('=== showNextUser completed ===');
        
        // Force browser repaint and ensure visibility with smooth animation
        setTimeout(function() {
            const card = $('#currentCard');
            card.css('visibility', 'visible')
                .css('display', 'block')
                .css('opacity', '1')
                .show();
            
            // Force reflow
            card[0].offsetHeight;
            
            // Ensure avatar is visible
            $('#userAvatar').css('visibility', 'visible')
                           .show();
                           
            // Scroll to top of card smoothly
            $('html, body').animate({
                scrollTop: card.offset().top - 100
            }, 300);
            
            // Force DOM update
            card.trigger('DOMNodeInserted');
        }, 10);
        
        // Additional DOM refresh for smooth appearance
        setTimeout(function() {
            const card = $('#currentCard')[0];
            if (card) {
                // Force browser to redraw the element
                card.style.display = 'none';
                card.offsetHeight; // Trigger reflow
                card.style.display = 'block';
            }
        }, 50);
    }