# @scoutai/auth

Authentication primitives: password hashing, session storage contracts, and cookie options.

The default `Argon2PasswordHasher` is a swappable implementation — production may substitute
another `PasswordHasher` or external identity provider without changing call sites.
