# @scoutai/notifications

Notification delivery abstraction for email, SMS, and in-app channels.

Defines `NotificationProvider` and a `MockNotificationProvider` that records sent messages
in memory. `getSent()` is exported for test assertions.
