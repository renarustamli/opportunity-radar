"""
Email digests via Resend.

Credentials come from the environment: RESEND_API_KEY and DIGEST_TO. Sending
from onboarding@resend.dev works without owning a domain, but Resend only
delivers it to the address the account was registered with.
"""

import os
from html import escape

import resend

SENDER = "Opportunity Radar <onboarding@resend.dev>"


def format_digest(scored_opportunities):
    """Build the HTML body. Takes (score, reasoning, opportunity) tuples."""
    blocks = []
    for score, reasoning, opp in scored_opportunities:
        prize = opp["prize_amount"] or "no prize listed"
        reason_line = f"<div><em>{escape(reasoning)}</em></div>" if reasoning else ""

        blocks.append(
            f"<li style='margin-bottom:18px'>"
            f"<div><strong>{escape(opp['title'])}</strong> &mdash; {score}</div>"
            f"<div>{escape(str(opp['deadline_text']))} &middot; {escape(str(prize))} "
            f"&middot; {escape(str(opp['organization'] or 'unknown'))}</div>"
            f"{reason_line}"
            f"<div><a href='{escape(opp['url'])}'>{escape(opp['url'])}</a></div>"
            f"</li>"
        )

    noun = "opportunity" if len(blocks) == 1 else "opportunities"
    return f"<h2>{len(blocks)} new {noun}</h2><ul>{''.join(blocks)}</ul>"


def send_digest(scored_opportunities):
    """Send the digest. Returns the Resend response, or None if nothing to send."""
    if not scored_opportunities:
        return None

    api_key = os.environ.get("RESEND_API_KEY")
    recipient = os.environ.get("DIGEST_TO")
    if not api_key or not recipient:
        raise RuntimeError("RESEND_API_KEY and DIGEST_TO must both be set")

    resend.api_key = api_key

    count = len(scored_opportunities)
    noun = "hackathon" if count == 1 else "hackathons"

    return resend.Emails.send({
        "from": SENDER,
        "to": [recipient],
        "subject": f"{count} new {noun} matching your profile",
        "html": format_digest(scored_opportunities),
    })
