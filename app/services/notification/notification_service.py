from typing import List, Optional


class NotificationService:
    """Handles all notification dispatching — email, in-app, push."""

    @staticmethod
    def send_email(to: str, subject: str, body: str) -> None:
        # TODO: integrate with email provider (SendGrid, SES, etc.)
        print(f"[EMAIL] To: {to} | Subject: {subject}")

    @staticmethod
    def send_bulk_email(recipients: List[str], subject: str, body: str) -> None:
        for recipient in recipients:
            NotificationService.send_email(recipient, subject, body)

    @staticmethod
    def notify_quiz_scheduled(student_emails: List[str], quiz_title: str, scheduled_at: str) -> None:
        subject = f"Quiz Scheduled: {quiz_title}"
        body = f"Your quiz '{quiz_title}' is scheduled for {scheduled_at}."
        NotificationService.send_bulk_email(student_emails, subject, body)

    @staticmethod
    def notify_quiz_result(student_email: str, quiz_title: str, score: int, total: int) -> None:
        subject = f"Quiz Result: {quiz_title}"
        body = f"You scored {score}/{total} in '{quiz_title}'."
        NotificationService.send_email(student_email, subject, body)

    @staticmethod
    def notify_password_reset(email: str, reset_token: str) -> None:
        subject = "Password Reset Request"
        body = f"Your password reset token: {reset_token}"
        NotificationService.send_email(email, subject, body)

    @staticmethod
    def notify_classroom_assignment(student_email: str, classroom_name: str) -> None:
        subject = "Classroom Assignment"
        body = f"You have been assigned to classroom: {classroom_name}"
        NotificationService.send_email(student_email, subject, body)
