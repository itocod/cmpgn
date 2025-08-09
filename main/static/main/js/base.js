
// Persistent follow state management
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all follow buttons
    document.querySelectorAll('.follow-btn').forEach(button => {
        const userId = button.getAttribute('data-user-id');
        
        // Get server-side initial state
        const serverState = button.getAttribute('data-is-following') === 'true';
        
        // Check localStorage for updated state
        const storageKey = `followState_${userId}`;
        const storedState = localStorage.getItem(storageKey);
        
        // Determine which state to use (stored state takes precedence)
        const initialState = storedState !== null ? 
            storedState === 'true' : 
            serverState;
        
        // Apply initial state
        button.classList.toggle('following', initialState);
        button.textContent = initialState ? 'Following' : 'Follow';
        button.setAttribute('data-is-following', initialState.toString());

        // Add click handler
        button.addEventListener('click', async function() {
            const userId = this.getAttribute('data-user-id');
            const isFollowing = this.getAttribute('data-is-following') === 'true';
            const action = isFollowing ? 'unfollow' : 'follow';
            
            // Add loading state
            const originalText = this.textContent;
            this.disabled = true;
            this.classList.add('loading');
            this.textContent = '...';
            
            try {
                const response = await fetch('/toggle_follow/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': '{{ csrf_token }}'
                    },
                    body: JSON.stringify({
                        'user_id': userId,
                        'action': action
                    })
                });

                const data = await response.json();
                
                if (data.status === 'success') {
                    // Update button state
                    const newState = data.is_following;
                    this.classList.toggle('following', newState);
                    this.textContent = newState ? 'Following' : 'Follow';
                    this.setAttribute('data-is-following', newState.toString());
                    
                    // Update followers count
                    const followersCount = document.getElementById(`followers-count-${userId}`);
                    if (followersCount) {
                        followersCount.textContent = `(${data.followers_count} followers)`;
                    }
                    
                    // Persist state in localStorage
                    localStorage.setItem(`followState_${userId}`, newState.toString());
                } else {
                    console.error('Error:', data.message);
                    this.textContent = originalText;
                }
            } catch (error) {
                console.error('Error:', error);
                this.textContent = originalText;
            } finally {
                this.disabled = false;
                this.classList.remove('loading');
            }
        });
    });
});
