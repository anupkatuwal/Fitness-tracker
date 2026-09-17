"""End-to-end API tests over the seeded database."""

from datetime import date, timedelta

import pytest

from app.database import SessionLocal
from app.models import Exercise, PEDProfile
from seed import EXERCISES, PED_PROFILES, _upsert


@pytest.fixture()
def seeded(client):
    with SessionLocal() as session:
        _upsert(session, Exercise, EXERCISES)
        _upsert(session, PEDProfile, PED_PROFILES)
        session.commit()
    return client


# ------------------------------------------------------------------------------ auth
def test_register_login_and_me(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "New@Example.com", "username": "newlifter", "password": "Str0ngPass!"},
    )
    assert response.status_code == 201
    assert response.json()["token_type"] == "bearer"
    assert response.json()["user"]["email"] == "new@example.com"

    # Login works with either the email or the username.
    for identifier in ("new@example.com", "newlifter", "NEWLIFTER"):
        login = client.post("/api/auth/login", data={"username": identifier, "password": "Str0ngPass!"})
        assert login.status_code == 200, identifier

    token = login.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "newlifter"


def test_duplicate_registration_conflicts(client, auth_headers):
    dup_email = client.post(
        "/api/auth/register",
        json={"email": "lifter@example.com", "username": "different", "password": "Str0ngPass!"},
    )
    assert dup_email.status_code == 409

    dup_username = client.post(
        "/api/auth/register",
        json={"email": "different@example.com", "username": "lifter", "password": "Str0ngPass!"},
    )
    assert dup_username.status_code == 409


def test_bad_password_and_missing_token_are_rejected(client, auth_headers):
    assert client.post(
        "/api/auth/login", data={"username": "lifter@example.com", "password": "wrong"}
    ).status_code == 401
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer nonsense"}).status_code == 401


def test_update_goals(client, auth_headers):
    response = client.patch(
        "/api/auth/me", headers=auth_headers, json={"goal_calories": 3000, "weight_kg": 82.5}
    )
    assert response.status_code == 200
    assert response.json()["goal_calories"] == 3000
    assert response.json()["weight_kg"] == 82.5
    # Untouched goals keep their defaults.
    assert response.json()["goal_protein_g"] == 180


# ------------------------------------------------------------------------- exercises
def test_exercise_directory_and_filters(seeded):
    all_exercises = seeded.get("/api/exercises").json()
    assert len(all_exercises) == 10
    assert all(e["form_instructions"] for e in all_exercises)

    filters = seeded.get("/api/exercises/filters").json()
    assert "Barbell" in filters["equipment"]
    assert "Chest" in filters["muscle_groups"]

    chest = seeded.get("/api/exercises", params={"muscle_group": "chest"}).json()
    assert chest and all(e["muscle_group"] == "Chest" for e in chest)

    barbell_chest = seeded.get(
        "/api/exercises", params={"muscle_group": "Chest", "equipment": "Barbell"}
    ).json()
    assert len(barbell_chest) == 1
    assert barbell_chest[0]["slug"] == "barbell-bench-press"

    assert seeded.get("/api/exercises", params={"search": "squat"}).json()
    assert seeded.get("/api/exercises/barbell-back-squat").status_code == 200
    assert seeded.get("/api/exercises/does-not-exist").status_code == 404


# ------------------------------------------------------------------------------ peds
def test_ped_library_always_carries_hazard_information(seeded):
    profiles = seeded.get("/api/peds").json()
    assert len(profiles) == 10
    for profile in profiles:
        assert profile["cardiovascular_risk"].strip(), profile["name"]
        assert profile["endocrine_risk"].strip(), profile["name"]
        assert profile["hepatic_risk"].strip(), profile["name"]
        assert profile["legal_status"].strip(), profile["name"]
        assert profile["harm_reduction_notes"].strip(), profile["name"]


def test_ped_detail_and_filters(seeded):
    detail = seeded.get("/api/peds/trenbolone-acetate").json()
    assert detail["name"] == "Trenbolone Acetate"
    assert detail["medical_supervision_required"] is True

    categories = seeded.get("/api/peds/categories").json()
    assert "AAS" in categories

    aas = seeded.get("/api/peds", params={"category": "AAS"}).json()
    assert aas and all(p["category"] == "AAS" for p in aas)

    assert seeded.get("/api/peds", params={"search": "deca"}).json()
    assert seeded.get("/api/peds/not-a-compound").status_code == 404
    assert "not medical advice" in seeded.get("/api/peds/disclaimer").json()["disclaimer"].lower()


# ---------------------------------------------------------------------------- macros
def test_macro_log_summary_and_trend(client, auth_headers):
    today = date.today()
    yesterday = today - timedelta(days=1)

    client.post(
        "/api/macros/logs",
        headers=auth_headers,
        json={
            "food_name": "Chicken Breast",
            "serving_size_g": 200,
            "servings": 1,
            "meal_type": "lunch",
            "calories": 330,
            "protein_g": 62,
            "carbs_g": 0,
            "fats_g": 7.2,
            "fiber_g": 0,
        },
    )
    client.post(
        "/api/macros/logs",
        headers=auth_headers,
        json={
            "food_name": "Rolled Oats",
            "calories": 389,
            "protein_g": 16.9,
            "carbs_g": 66.3,
            "fats_g": 6.9,
            "fiber_g": 10.6,
            "logged_on": yesterday.isoformat(),
        },
    )

    summary = client.get("/api/macros/summary", headers=auth_headers).json()
    assert summary["day"] == today.isoformat()
    assert summary["totals"]["calories"] == 330
    assert summary["totals"]["protein_g"] == 62
    assert len(summary["entries"]) == 1
    assert summary["goals"]["calories"] == 2500

    past = client.get(
        "/api/macros/summary", headers=auth_headers, params={"day": yesterday.isoformat()}
    ).json()
    assert past["totals"]["calories"] == 389

    trend = client.get("/api/macros/trend", headers=auth_headers, params={"days": 7}).json()
    assert len(trend["points"]) == 7
    assert trend["points"][-1]["day"] == today.isoformat()
    assert trend["points"][-1]["calories"] == 330
    assert trend["points"][-2]["calories"] == 389
    assert trend["points"][0]["calories"] == 0  # empty days are filled with zeros


def test_macro_logs_are_scoped_to_their_owner(client, auth_headers):
    created = client.post(
        "/api/macros/logs", headers=auth_headers, json={"food_name": "Steak", "calories": 500}
    )
    log_id = created.json()["id"]

    other = client.post(
        "/api/auth/register",
        json={"email": "other@example.com", "username": "other", "password": "Str0ngPass!"},
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}

    assert client.get("/api/macros/logs", headers=other_headers).json() == []
    # A second user cannot delete someone else's entry.
    assert client.delete(f"/api/macros/logs/{log_id}", headers=other_headers).status_code == 404
    assert client.delete(f"/api/macros/logs/{log_id}", headers=auth_headers).status_code == 204


def test_macro_endpoints_require_authentication(client):
    assert client.get("/api/macros/logs").status_code == 401
    assert client.get("/api/macros/summary").status_code == 401
    assert client.get("/api/macros/search", params={"q": "oats"}).status_code == 401


def test_invalid_macro_payload_is_rejected(client, auth_headers):
    assert client.post(
        "/api/macros/logs", headers=auth_headers, json={"food_name": "X", "servings": 0}
    ).status_code == 422
    assert client.post(
        "/api/macros/logs", headers=auth_headers, json={"food_name": "X", "calories": -5}
    ).status_code == 422


# ----------------------------------------------------------------------- calculators
def test_tdee_matches_mifflin_st_jeor(client):
    response = client.post(
        "/api/calculators/tdee",
        json={
            "sex": "male",
            "age": 28,
            "height_cm": 180,
            "weight_kg": 80,
            "activity_level": "moderate",
            "goal": "maintain",
        },
    )
    body = response.json()
    # (10 x 80) + (6.25 x 180) - (5 x 28) + 5 = 1790
    assert body["bmr"] == 1790.0
    assert body["tdee"] == pytest.approx(1790 * 1.55, abs=0.1)
    assert body["target_calories"] == pytest.approx(body["tdee"], abs=0.1)
    assert body["protein_g"] == 160.0  # 2 g/kg


def test_tdee_female_and_cut_goal(client):
    body = client.post(
        "/api/calculators/tdee",
        json={
            "sex": "female",
            "age": 30,
            "height_cm": 165,
            "weight_kg": 60,
            "activity_level": "sedentary",
            "goal": "cut",
        },
    ).json()
    # (10 x 60) + (6.25 x 165) - (5 x 30) - 161 = 1320.25
    assert body["bmr"] == pytest.approx(1320.25, abs=0.1)
    assert body["target_calories"] == pytest.approx(body["tdee"] * 0.8, abs=0.1)


def test_calculator_rejects_impossible_input(client):
    assert client.post(
        "/api/calculators/tdee",
        json={"sex": "other", "age": 28, "height_cm": 180, "weight_kg": 80},
    ).status_code == 422
    assert client.post(
        "/api/calculators/tdee",
        json={"sex": "male", "age": 28, "height_cm": 0, "weight_kg": 80},
    ).status_code == 422
