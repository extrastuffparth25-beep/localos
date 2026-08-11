"""
review_responder.py — AI Google Review Response Generator for LOCALOS.

Generates professional, personalized responses to both positive and
negative Google reviews. Maintains the business's voice while being
warm, authentic, and non-generic.
"""

from __future__ import annotations

import random


# ──────────────────────────────────────────────
# Positive Review Response Templates
# ──────────────────────────────────────────────
POSITIVE_TEMPLATES = [
    # 5-star warmth
    "Thank you so much for the wonderful review, {reviewer}! 🙏 We're thrilled to hear you had a great experience at {business}. Your kind words mean the world to our team. We can't wait to see you again!",

    "Wow, thank you {reviewer}! We love hearing feedback like this. Our team works hard to deliver the best experience possible, and it's so rewarding to know it shows. See you next time! 😊",

    "{reviewer}, thank you for taking the time to leave us such a kind review! We're genuinely grateful for your support. It's customers like you that make what we do so fulfilling. Hope to see you again soon!",

    "What a wonderful thing to read, {reviewer}! Thank you for your generous review. We're delighted you chose {business} and we look forward to welcoming you back. 🌟",

    "We really appreciate the kind words, {reviewer}! Making sure our customers have a fantastic experience is our top priority, and your review confirms we're on the right track. Thank you! 🙌",

    "Thank you for the 5-star review, {reviewer}! It's always great to hear from happy customers. We put a lot of care into everything we do, and it's great to know you noticed. See you next time!",

    "{reviewer}, thank you so much! Reviews like yours make our day. We're so glad you had a positive experience with {business}. We'll make sure your next visit is just as good! ❤️",
]

# ──────────────────────────────────────────────
# Negative Review Response Templates (Diplomatic)
# ──────────────────────────────────────────────
NEGATIVE_TEMPLATES = [
    # 1-2 star — acknowledge, apologize, offer resolution
    "{reviewer}, thank you for sharing your feedback. We're sorry to hear your experience didn't meet expectations. This isn't the standard we hold ourselves to. We'd love the chance to make it right — could you reach out to us directly at {contact} so we can address your concerns personally?",

    "We appreciate your honest feedback, {reviewer}. We're genuinely sorry about your experience. Every customer matters to us, and we'd like to understand what went wrong so we can improve. Please contact us at {contact} and we'll do our best to resolve this for you.",

    "Thank you for letting us know, {reviewer}. We take feedback very seriously, and we're sorry we fell short this time. We'd really appreciate the opportunity to make things right. Please reach out to us at {contact} — we want to earn back your trust.",

    "{reviewer}, we're sorry to hear this. Your experience doesn't reflect the quality we strive for at {business}. We've taken note of your feedback and would love to discuss this further. Please contact us at {contact} so we can address your concerns directly.",

    "We hear you, {reviewer}, and we're sorry. Thank you for being upfront about your experience — it helps us improve. We'd genuinely like to make this right for you. Please don't hesitate to reach out to us at {contact}.",
]

# ──────────────────────────────────────────────
# Neutral / 3-star Response Templates
# ──────────────────────────────────────────────
NEUTRAL_TEMPLATES = [
    "Thank you for your feedback, {reviewer}! We're glad to hear some aspects of your visit were positive. We're always working to improve, and your input helps us do that. If there's anything specific we can do better next time, please let us know at {contact}.",

    "{reviewer}, thank you for taking the time to share your thoughts. We're happy to hear you had some positive moments, and we'd love to earn that 5-star experience next time. If there's anything we can improve, please don't hesitate to reach out at {contact}.",

    "We appreciate the feedback, {reviewer}! We aim for a 5-star experience every time, and your review helps us see where we can do better. We hope to exceed your expectations on your next visit to {business}.",
]


def generate_review_response(
    reviewer_name: str,
    rating: int,
    review_text: str,
    business_name: str,
    contact_info: str = "our team directly",
) -> str:
    """
    Generate a personalized review response.

    Args:
        reviewer_name: Name of the reviewer
        rating: 1-5 star rating
        review_text: The review content (used for future sentiment analysis)
        business_name: Your business name
        contact_info: Contact method for resolution (email/phone)

    Returns a response string ready to post.
    """
    first_name = reviewer_name.split()[0] if reviewer_name else "there"

    if rating >= 4:
        template = random.choice(POSITIVE_TEMPLATES)
    elif rating == 3:
        template = random.choice(NEUTRAL_TEMPLATES)
    else:
        template = random.choice(NEGATIVE_TEMPLATES)

    response = template.format(
        reviewer=first_name,
        business=business_name,
        contact=contact_info,
    )

    return response


def generate_batch_responses(
    reviews: list[dict[str, str | int]],
    business_name: str,
    contact_info: str = "our team directly",
) -> list[dict[str, str]]:
    """
    Generate responses for a batch of reviews.

    Args:
        reviews: List of dicts with 'reviewer_name', 'rating', 'review_text'
        business_name: Your business name
        contact_info: Contact method

    Returns list of dicts with 'reviewer_name', 'rating', 'response'.
    """
    results = []
    for review in reviews:
        response = generate_review_response(
            reviewer_name=review.get("reviewer_name", "Valued Customer"),
            rating=int(review.get("rating", 5)),
            review_text=review.get("review_text", ""),
            business_name=business_name,
            contact_info=contact_info,
        )
        results.append({
            "reviewer_name": review.get("reviewer_name", ""),
            "rating": review.get("rating", ""),
            "response": response,
        })

    return results


def format_review_responses(
    reviews: list[dict[str, str | int]],
    business_name: str,
) -> str:
    """Format all review responses for easy copy-paste."""
    responses = generate_batch_responses(reviews, business_name)

    lines = []
    lines.append(f"{'═' * 60}")
    lines.append(f"⭐ REVIEW RESPONSES — {business_name}")
    lines.append(f"{'═' * 60}")

    for i, resp in enumerate(responses, 1):
        rating_stars = '⭐' * int(resp.get('rating', 0))
        lines.append(f"\n{'─' * 50}")
        lines.append(f"📝 Review {i}: {resp['reviewer_name']} — {rating_stars}")
        lines.append(f"{'─' * 50}")
        lines.append(f"\n{resp['response']}")

    lines.append(f"\n{'═' * 60}\n")
    return "\n".join(lines)
