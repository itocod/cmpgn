// Singleton pattern to ensure single instance
const CommentSystem = (function() {
    let instance;
    
    function createInstance() {
        // Private variables
        let initialized = false;
        let currentCampaignId = null;
        
        // Initialize the comment system
        function init() {
            if (initialized) return;
            
            // Event delegation for all comment-related events
            document.addEventListener('click', handleClickEvents);
            document.addEventListener('submit', handleSubmitEvents);
            
            // Close popup when clicking outside
            const popup = document.getElementById('commentPopup');
            if (popup) {
                popup.addEventListener('click', function(e) {
                    if (e.target === this) {
                        this.style.display = 'none';
                    }
                });
            }
            
            // Close popup with close button
            const closeBtn = document.querySelector('.close-comment-popup');
            if (closeBtn) {
                closeBtn.addEventListener('click', function() {
                    document.getElementById('commentPopup').style.display = 'none';
                });
            }
            
            initialized = true;
        }
        
        // Handle all click events
        function handleClickEvents(e) {
            // Like buttons
            if (e.target.closest('.like-comment-btn')) {
                e.preventDefault();
                const btn = e.target.closest('.like-comment-btn');
                handleLikeDislike(btn, 'like');
            }
            
            // Dislike buttons
            if (e.target.closest('.dislike-comment-btn')) {
                e.preventDefault();
                const btn = e.target.closest('.dislike-comment-btn');
                handleLikeDislike(btn, 'dislike');
            }
            
            // Reply buttons
            if (e.target.closest('.reply-comment-btn')) {
                e.preventDefault();
                const btn = e.target.closest('.reply-comment-btn');
                showReplyForm(btn);
            }
            
            // View replies buttons
            if (e.target.closest('.view-replies-btn')) {
                e.preventDefault();
                const btn = e.target.closest('.view-replies-btn');
                toggleReplies(btn);
            }
            
            // Cancel reply buttons
            if (e.target.closest('.cancel-reply-btn')) {
                e.preventDefault();
                const btn = e.target.closest('.cancel-reply-btn');
                btn.closest('.reply-form-container').style.display = 'none';
            }
        }
        
        // Handle all submit events
        function handleSubmitEvents(e) {
            // Main comment form
            if (e.target.matches('#commentForm')) {
                e.preventDefault();
                handleCommentSubmit(e.target);
            }
            
            // Reply forms
            if (e.target.matches('.reply-form')) {
                e.preventDefault();
                submitReplyForm(e.target);
            }
        }
        
        // Show comment popup
        function showCommentPopup(campaignId) {
            init(); // Ensure system is initialized
            currentCampaignId = campaignId;
            
            const popup = document.getElementById('commentPopup');
            const campaignIdInput = document.getElementById('campaignIdInput');
            
            if (popup && campaignIdInput) {
                campaignIdInput.value = campaignId;
                popup.style.display = 'flex';
                loadComments(campaignId);
            }
        }
        
        // Load comments for a campaign
        function loadComments(campaignId) {
            const commentList = document.getElementById('commentList');
            if (!commentList) return;
            
            commentList.innerHTML = '<div class="loading-comments">Loading comments...</div>';
            
            fetch(`/get_comments/?campaign_id=${campaignId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.comments?.length > 0) {
                        commentList.innerHTML = data.comments.map(createCommentHtml).join('');
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
                            <button onclick="CommentSystem.loadComments(${campaignId})" class="retry-btn">
                                <i class="fas fa-sync-alt"></i> Retry
                            </button>
                        </div>
                    `;
                });
        }
        
        // Create HTML for a comment
        function createCommentHtml(comment) {
            const timestamp = new Date(comment.timestamp);
            const formattedDate = timestamp.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            
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
                            <img src="${document.querySelector('.current-user-img')?.src || ''}" alt="Your profile picture" class="current-user-img">
                            <span>Replying to ${comment.user_username}</span>
                        </div>
                        <form class="reply-form" data-comment-id="${comment.id}">
                            <input type="hidden" name="campaign_id" value="${currentCampaignId}">
                            <input type="hidden" name="parent_comment_id" value="${comment.id}">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''}">
                            <textarea name="text" class="reply-textarea" placeholder="Write your reply here..."></textarea>
                            <button type="submit" class="submit-reply-btn">Post Reply</button>
                            <button type="button" class="cancel-reply-btn">Cancel</button>
                        </form>
                    </div>
                    
                    <div class="replies-container" id="replies-${comment.id}" style="display: none;"></div>
                </div>
            `;
        }
        
        // Handle comment form submission
        function handleCommentSubmit(form) {
            const formData = new FormData(form);
            const campaignId = formData.get('campaign_id');
            
            fetch('/post_comment/', {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': formData.get('csrfmiddlewaretoken') },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    form.querySelector('textarea').value = '';
                    loadComments(campaignId);
                } else {
                    alert('Error posting comment: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error posting comment. Please try again.');
            });
        }
        
        // Handle reply form submission
        function submitReplyForm(form) {
            const formData = new FormData(form);
            const commentId = form.dataset.commentId;
            
            fetch('/post_comment/', {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': formData.get('csrfmiddlewaretoken') },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    form.querySelector('textarea').value = '';
                    document.getElementById(`reply-form-${commentId}`).style.display = 'none';
                    loadComments(currentCampaignId);
                } else {
                    alert('Failed to post reply. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error submitting reply:', error);
                alert('Network error. Please check your connection and try again.');
            });
        }
        
        // Handle like/dislike actions
        function handleLikeDislike(btn, action) {
            const commentId = btn.dataset.commentId;
            const isActive = btn.classList.contains('active');
            const finalAction = isActive ? 'remove' : action;
            
            const formData = new FormData();
            formData.append('comment_id', commentId);
            formData.append('action', finalAction);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
            
            fetch('/like_dislike_comment/', {
                method: 'POST',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const commentItem = btn.closest('.comment-item');
                    const likeBtn = commentItem.querySelector('.like-comment-btn');
                    const dislikeBtn = commentItem.querySelector('.dislike-comment-btn');
                    
                    // Update counts
                    if (data.like_count !== undefined) {
                        commentItem.querySelector('.like-count').textContent = data.like_count;
                    }
                    if (data.dislike_count !== undefined) {
                        commentItem.querySelector('.dislike-count').textContent = data.dislike_count;
                    }
                    
                    // Update button states
                    if (finalAction === 'remove') {
                        btn.classList.remove('active');
                    } else if (finalAction === 'like') {
                        likeBtn.classList.add('active');
                        dislikeBtn.classList.remove('active');
                    } else {
                        dislikeBtn.classList.add('active');
                        likeBtn.classList.remove('active');
                    }
                }
            })
            .catch(console.error);
        }
        
        // Show reply form
        function showReplyForm(btn) {
            const commentId = btn.dataset.commentId;
            const replyForm = document.getElementById(`reply-form-${commentId}`);
            
            if (!replyForm) return;
            
            // Hide all other reply forms
            document.querySelectorAll('.reply-form-container').forEach(form => {
                if (form.id !== `reply-form-${commentId}`) {
                    form.style.display = 'none';
                }
            });
            
            // Toggle this reply form
            replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
        }
        
        // Toggle replies visibility
        function toggleReplies(btn) {
            const commentId = btn.dataset.commentId;
            const repliesContainer = document.getElementById(`replies-${commentId}`);
            
            if (repliesContainer.style.display === 'none') {
                if (repliesContainer.innerHTML === '') {
                    loadReplies(commentId);
                }
                repliesContainer.style.display = 'block';
                btn.innerHTML = `<i class="fas fa-comments"></i> Hide replies`;
            } else {
                repliesContainer.style.display = 'none';
                const replyCount = parseInt(btn.textContent.match(/\d+/)[0]);
                btn.innerHTML = `<i class="fas fa-comments"></i> ${replyCount} ${replyCount === 1 ? 'reply' : 'replies'}`;
            }
        }
        
        // Load replies for a comment
        function loadReplies(commentId) {
            const repliesContainer = document.getElementById(`replies-${commentId}`);
            if (!repliesContainer) return;
            
            repliesContainer.innerHTML = '<div class="loading-replies">Loading replies...</div>';
            
            fetch(`/get_replies/${commentId}/`)
                .then(response => response.json())
                .then(data => {
                    repliesContainer.innerHTML = data.replies?.length > 0 
                        ? data.replies.map(createCommentHtml).join('') 
                        : `<div class="no-replies"><p>No replies yet.</p></div>`;
                })
                .catch(error => {
                    console.error('Error loading replies:', error);
                    repliesContainer.innerHTML = `
                        <div class="error-loading-replies">
                            <i class="fas fa-exclamation-triangle"></i>
                            <p>Error loading replies. Please try again.</p>
                            <button onclick="CommentSystem.loadReplies(${commentId})" class="retry-btn">
                                <i class="fas fa-sync-alt"></i> Retry
                            </button>
                        </div>
                    `;
                });
        }
        
        return {
            showCommentPopup,
            loadComments,
            loadReplies
        };
    }
    
    return {
        getInstance: function() {
            if (!instance) {
                instance = createInstance();
            }
            return instance;
        }
    };
})();

// Initialize the singleton instance
const commentSystem = CommentSystem.getInstance();

// Expose the showCommentPopup function globally
window.CommentSystem = {
    showCommentPopup: commentSystem.showCommentPopup,
    loadComments: commentSystem.loadComments,
    loadReplies: commentSystem.loadReplies
};