SELECT users.id, users.username, follows.user_being_followed_id, follows.user_following_id
FROM users
LEFT JOIN follows
ON users.id = follows.user_being_followed_id
WHERE users.id = 1;
LIMIT 3; 

# all the users that user with id129 is following
SELECT users.id, users.username, follows.user_being_followed_id
LEFT JOIN follows
ON users.id = follows.user_being_followed_id
WHERE follows.user_following_id = 129;


#u129's followers - id 129
SELECT users.id, users.username, follows.user_being_followed_id
LEFT JOIN follows
ON users.id = follows.user_following_id
WHERE follows.user_being_followed_id = 129;


followers = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follows.user_being_followed_id == id),
        secondaryjoin=(Follows.user_following_id == id)
    )

