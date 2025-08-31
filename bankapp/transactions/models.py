from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet


class Transaction(models.Model):
    TYPES = [
        ("DEPOSIT", "Deposit"),
        ("WITHDRAW", "Withdraw"),
        ("TRANSFER", "Transfer"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.BinaryField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="received_transactions",
        on_delete=models.SET_NULL,
    )

    # FLAW 4 FIX
    def set_note(self, note_text):
        if not note_text:
            return

        f = Fernet(settings.FERNET_SECRET_KEY.encode())

        if isinstance(note_text, bytes):
            note_text = note_text.decode()

        self.note = f.encrypt(note_text.encode())


    def get_note(self) -> str:
        if self.note:
            try:
                f = Fernet(settings.FERNET_SECRET_KEY.encode())
                return f.decrypt(self.note).decode()
            except Exception:
                return "[Could not decrypt]"
        return ""

    def __str__(self):
            return f"{self.user.username} - {self.transaction_type} - {self.amount}"
