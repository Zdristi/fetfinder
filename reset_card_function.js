        }
        
        // Reset card to initial state
        function resetCard() {
            console.log('Resetting card styles and classes');
            // Completely reset card to initial state
            $('#currentCard').removeClass('swipe-card-liked swipe-card-disliked')
                            .css({
                                'transform': 'translateX(0) rotate(0deg)',
                                'transition': 'none',
                                'display': 'block',
                                'opacity': '1',
                                'position': 'relative',
                                'margin': '20px auto',
                                'max-width': '400px'
                            })
                            .show();
            
            // Reset avatar
            $('#userAvatar').css({
                'width': '100%',
                'height': '300px',
                'background-size': 'cover',
                'background-position': 'center',
                'border-radius': '10px 10px 0 0'
            });
            
            // Reset user info
            $('.user-info').css({
                'padding': '20px'
            });
            
            // Force reflow
            $('#currentCard')[0].offsetHeight;
        }
        
    }