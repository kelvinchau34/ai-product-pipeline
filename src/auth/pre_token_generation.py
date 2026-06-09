"""
Cognito Pre Token Generation Lambda trigger.

Called by Cognito *before* issuing every JWT (login and token refresh).
Adds a simplified 'custom:role' claim so the frontend doesn't need to
inspect the raw 'cognito:groups' array on every render.

Cognito event shape (V1 trigger):
  event['request']['groupConfiguration']['groupsToOverride'] → list of group names

Why a Lambda trigger instead of just reading cognito:groups in the frontend?
  - The custom:role claim is always in sync with group membership (no stale cache).
  - The API Gateway Cognito Authorizer can enforce role checks without extra code.
  - Demonstrates the serverless trigger pattern for portfolio/interview purposes.
"""


def lambda_handler(event: dict, context) -> dict:
    groups: list[str] = (
        event.get("request", {})
        .get("groupConfiguration", {})
        .get("groupsToOverride", [])
    )

    role = "manager" if "managers" in groups else "colleague"

    event["response"]["claimsOverrideDetails"] = {
        "claimsToAddOrOverride": {
            "custom:role": role,
        }
    }

    return event
