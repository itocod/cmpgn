    // Function to show comment popup
function showCommentPopup(campaignId) {
    const popup = document.getElementById('commentPopup');
    const campaignIdInput = document.getElementById('campaignIdInput');
    
    // Set the campaign ID in the form
    campaignIdInput.value = campaignId;
    
    // Show the popup
    popup.style.display = 'flex';
    
    // Load comments for this campaign
    loadComments(campaignId);
}

// Function to load comments
function loadComments(campaignId) {
    const commentList = document.getElementById('commentList');
    commentList.innerHTML = '<div class="loading-comments">Loading comments...</div>';
    
    fetch(`/get_comments/?campaign_id=${campaignId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.comments && data.comments.length > 0) {
                let commentsHtml = '';
                
                data.comments.forEach(comment => {
                    commentsHtml += createCommentHtml(comment);
                });
                
                commentList.innerHTML = commentsHtml;
                
                // Add event listeners for like/dislike buttons
                document.querySelectorAll('.like-comment-btn').forEach(btn => {
                    btn.addEventListener('click', handleLikeDislike);
                });
                
                document.querySelectorAll('.dislike-comment-btn').forEach(btn => {
                    btn.addEventListener('click', handleLikeDislike);
                });
                
                // Add event listeners for reply buttons
                document.querySelectorAll('.reply-comment-btn').forEach(btn => {
                    btn.addEventListener('click', showReplyForm);
                });
                
                // Add event listeners for view replies buttons
                document.querySelectorAll('.view-replies-btn').forEach(btn => {
                    btn.addEventListener('click', toggleReplies);
                });
            } else {
                commentList.innerHTML = `
                    <div class="no-comments">
                        <i class="far fa-comment-dots"></i>
                        <p>No comments yet. Be the first to comment!</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading comments:', error);
            commentList.innerHTML = `
                <div class="error-loading-comments">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error loading comments. Please try again.</p>
                    <button onclick="loadComments(${campaignId})" class="retry-btn">
                        <i class="fas fa-sync-alt"></i> Retry
                    </button>
                </div>
            `;
        });
}

// Function to create HTML for a comment
function createCommentHtml(comment) {
    const timestamp = new Date(comment.timestamp);
    const formattedDate = timestamp.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    // Determine like/dislike button states
    const likeBtnClass = comment.user_like_status === 'liked' ? 'active' : '';
    const dislikeBtnClass = comment.user_like_status === 'disliked' ? 'active' : '';
    
    return `
        <div class="comment-item" data-comment-id="${comment.id}">
            <div class="comment-header">
                <a href="/user-profile/@${comment.user_username}/" class="comment-user-link">
                    <img src="${comment.user_profile_image || '/static/images/default_profile.png'}" 
                         alt="${comment.user_username}'s profile picture" 
                         class="comment-user-img"
                         onerror="this.onerror=null;this.src='/static/images/default_profile.png'">
                </a>
                <div class="comment-user-info">
                    <a href="/user-profile/@${comment.user_username}/" class="comment-user">${comment.user_username}</a>
                    <span class="comment-timestamp" title="${timestamp.toISOString()}">${formattedDate}</span>
                </div>
            </div>
            <div class="comment-text">${comment.text}</div>
            
            <div class="comment-actions">
                <button class="like-comment-btn ${likeBtnClass}" data-comment-id="${comment.id}">
                    <i class="fas fa-thumbs-up"></i> <span class="like-count">${comment.like_count}</span>
                </button>
                <button class="dislike-comment-btn ${dislikeBtnClass}" data-comment-id="${comment.id}">
                    <i class="fas fa-thumbs-down"></i> <span class="dislike-count">${comment.dislike_count}</span>
                </button>
                <button class="reply-comment-btn" data-comment-id="${comment.id}">
                    <i class="fas fa-reply"></i> Reply
                </button>
                
                ${comment.reply_count > 0 ? `
                    <button class="view-replies-btn" data-comment-id="${comment.id}">
                        <i class="fas fa-comments"></i> ${comment.reply_count} ${comment.reply_count === 1 ? 'reply' : 'replies'}
                    </button>
                ` : ''}
            </div>
            
            <div class="reply-form-container" id="reply-form-${comment.id}" style="display: none;">
                <div class="current-user-preview">
                    <img src="${document.querySelector('.current-user-img').src}" alt="Your profile picture" class="current-user-img">
                    <span>Replying to ${comment.user_username}</span>
                </div>
<form class="reply-form" data-comment-id="${comment.id}">
    <input type="hidden" name="campaign_id" value="${document.getElementById('campaignIdInput').value}">
    <input type="hidden" name="parent_comment_id" value="${comment.id}">
    <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">
    <textarea name="text" class="reply-textarea" placeholder="Write your reply here..."></textarea>
    <button type="submit" class="submit-reply-btn">Post Reply</button>
    <button type="button" class="cancel-reply-btn">Cancel</button>
</form>

            </div>
            
            <div class="replies-container" id="replies-${comment.id}" style="display: none;"></div>
        </div>
    `;
}
function handleLikeDislike(e) {
    e.preventDefault();
    const btn = e.currentTarget;
    const commentId = btn.dataset.commentId;
    const isLikeBtn = btn.classList.contains('like-comment-btn');
    const action = btn.classList.contains('active') ? 'remove' : (isLikeBtn ? 'like' : 'dislike');
    
    const formData = new FormData();
    formData.append('comment_id', commentId);
    formData.append('action', action);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
    
    fetch('/like_dislike_comment/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',  // Add this header
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            const commentItem = btn.closest('.comment-item');
            const likeBtn = commentItem.querySelector('.like-comment-btn');
            const dislikeBtn = commentItem.querySelector('.dislike-comment-btn');
            const likeCount = commentItem.querySelector('.like-count');
            const dislikeCount = commentItem.querySelector('.dislike-count');
            
            // Update counts from server response
            if (data.like_count !== undefined) {
                likeCount.textContent = data.like_count;
            }
            if (data.dislike_count !== undefined) {
                dislikeCount.textContent = data.dislike_count;
            }
            
            // Update button states
            if (action === 'remove') {
                if (btn === likeBtn) {
                    likeBtn.classList.remove('active');
                } else {
                    dislikeBtn.classList.remove('active');
                }
            } else if (action === 'like') {
                likeBtn.classList.add('active');
                dislikeBtn.classList.remove('active');
            } else { // dislike
                dislikeBtn.classList.add('active');
                likeBtn.classList.remove('active');
            }
        } else {
            console.error('Error:', data.error);
            alert('Error processing your action. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Network error. Please check your connection and try again.');
    });
}
// Function to show reply form
function showReplyForm(e) {
    const commentId = e.currentTarget.dataset.commentId;
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    
    if (!replyForm) return; // Safety check

    // Hide all other reply forms first
    document.querySelectorAll('.reply-form-container').forEach(form => {
        if (form.id !== `reply-form-${commentId}`) {
            form.style.display = 'none';
        }
    });

    // Toggle this reply form
    replyForm.style.display = replyForm.style.display === 'none' || replyForm.style.display === '' ? 'block' : 'none';

    // Add event listener for the form submission
    const form = replyForm.querySelector('.reply-form');
    if (form) {
        form.onsubmit = function(e) {
            e.preventDefault();
            submitReplyForm(this);
        };
    }

    // Add event listener for cancel button
    const cancelBtn = replyForm.querySelector('.cancel-reply-btn');
    if (cancelBtn) {
        cancelBtn.onclick = function() {
            replyForm.style.display = 'none';
        };
    }
}


// Function to toggle replies visibility
function toggleReplies(e) {
    const commentId = e.currentTarget.dataset.commentId;
    const repliesContainer = document.getElementById(`replies-${commentId}`);
    
    if (repliesContainer.style.display === 'none') {
        // Load replies if not already loaded
        if (repliesContainer.innerHTML === '') {
            loadReplies(commentId);
        }
        repliesContainer.style.display = 'block';
        e.currentTarget.innerHTML = `<i class="fas fa-comments"></i> Hide replies`;
    } else {
        repliesContainer.style.display = 'none';
        const replyCount = parseInt(e.currentTarget.textContent.match(/\d+/)[0]);
        e.currentTarget.innerHTML = `<i class="fas fa-comments"></i> ${replyCount} ${replyCount === 1 ? 'reply' : 'replies'}`;
    }
}

// Function to load replies for a comment
function loadReplies(commentId) {
    const repliesContainer = document.getElementById(`replies-${commentId}`);
    repliesContainer.innerHTML = '<div class="loading-replies">Loading replies...</div>';
    
    fetch(`/get_replies/${commentId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.replies && data.replies.length > 0) {
                let repliesHtml = '';
                
                data.replies.forEach(reply => {
                    repliesHtml += createCommentHtml(reply);
                });
                
                repliesContainer.innerHTML = repliesHtml;
                
                // Add event listeners for like/dislike buttons in replies
                repliesContainer.querySelectorAll('.like-comment-btn').forEach(btn => {
                    btn.addEventListener('click', handleLikeDislike);
                });
                
                repliesContainer.querySelectorAll('.dislike-comment-btn').forEach(btn => {
                    btn.addEventListener('click', handleLikeDislike);
                });
            } else {
                repliesContainer.innerHTML = `
                    <div class="no-replies">
                        <p>No replies yet.</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading replies:', error);
            repliesContainer.innerHTML = `
                <div class="error-loading-replies">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error loading replies. Please try again.</p>
                    <button onclick="loadReplies(${commentId})" class="retry-btn">
                        <i class="fas fa-sync-alt"></i> Retry
                    </button>
                </div>
            `;
        });
}

// Handle main comment form submission
document.getElementById('commentForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const campaignId = formData.get('campaign_id');
    
    fetch('/post_comment/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear the textarea
            this.querySelector('textarea').value = '';
            // Reload comments
            loadComments(campaignId);
        } else {
            alert('Error posting comment: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error posting comment. Please try again.');
    });
});

// Close popup when clicking outside
document.getElementById('commentPopup').addEventListener('click', function(e) {
    if (e.target === this) {
        this.style.display = 'none';
    }
});

// Close popup with close button
document.querySelector('.close-comment-popup').addEventListener('click', function() {
    document.getElementById('commentPopup').style.display = 'none';
});
function submitReplyForm(form) {
    const formData = new FormData(form);
    const commentId = form.dataset.commentId;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch('/post_comment/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Refresh the comments to include the new reply
            const campaignId = document.getElementById('campaignIdInput').value;
            loadComments(campaignId);
        } else {
            alert('Failed to post reply. Please try again.');
            console.error('Reply post error:', data.error || data);
        }
    })
    .catch(error => {
        console.error('Error submitting reply:', error);
        alert('Network error. Please check your connection and try again.');
    });
}
