"""שליחת הודעות למשתמשים (AB#273).

כל הודעה נרשמת בטבלת notifications. שירות ההודעות (WhatsApp / SMS) קורא ממנה ושולח.
כך אפשר גם לבדוק בבדיקות ובממשק אילו הודעות נשלחו.
"""


def notify(conn, phone, message, channel="whatsapp"):
    """רישום הודעה לשליחה. מחזיר את מספר ההודעה."""
    row = conn.execute(
        """
        insert into notifications (phone, channel, message)
        values (%(phone)s, %(channel)s, %(message)s)
        returning id
        """,
        {"phone": phone, "channel": channel, "message": message},
    ).fetchone()
    return row["id"] if row else None
